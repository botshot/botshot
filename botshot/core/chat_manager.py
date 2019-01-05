import logging
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone
from django.utils.timezone import make_aware
from datetime import datetime
from botshot.core import config
from botshot.core.flow import get_flows
from botshot.core.message_processor import MessageProcessor
from botshot.core.parsing.message_parser import parse_text_entities
from botshot.core.parsing.raw_message import RawMessage
from botshot.core.persistence import todict
from botshot.core.responses import TextMessage, MessageElement
from botshot.models import ChatConversation, ChatUser, ChatMessage


class ChatManager:

    def __init__(self):
        from botshot.core.interceptors import AdminDialogInterceptor, BotshotVersionDialogInterceptor
        self.save_messages = config.get("SAVE_MESSAGES", True)
        # TODO: Register extra interceptors in config
        self.interceptors = [AdminDialogInterceptor(), BotshotVersionDialogInterceptor()]

    def accept(self, raw_message: RawMessage):
        """Parses a received message and accepts it for processing."""
        entities = self.parse_raw_message_entities(raw_message)
        logging.info("Parsed entities from message %s: %s", raw_message, entities)
        return self.accept_with_entities(raw_message, entities)

    def accept_with_entities(self, raw_message, entities):
        with transaction.atomic():
            try:
                conversation = ChatConversation.objects.select_for_update().get(
                    interface_name=raw_message.interface.name,
                    raw_conversation_id=raw_message.raw_conversation_id
                )
            except ObjectDoesNotExist:
                conversation = ChatConversation()
                conversation.interface_name = raw_message.interface.name
                conversation.raw_conversation_id = raw_message.raw_conversation_id
                conversation.meta = raw_message.conversation_meta
                raw_message.interface.fill_conversation_details(conversation)
                # Save and read instance from database to acquire lock
                conversation.save()
                logging.info("Created new conversation: %s", conversation.__dict__)
                conversation = ChatConversation.objects.select_for_update().get(pk=conversation.conversation_id)

            conversation.last_message_time = timezone.now()

            try:
                user = ChatUser.objects.get(raw_user_id=raw_message.raw_user_id)
            except ObjectDoesNotExist:
                user = ChatUser()
                user.raw_user_id = raw_message.raw_user_id
                # Save user before filling details so that image field can be saved
                user.save()
                # TODO: also update details of existing users every once in a while
                raw_message.interface.fill_user_details(user)
                logging.info("Created new user: %s", user.__dict__)
                user.save()
                user.conversations.add(conversation)
                user.save()
                conversation.save()

            message = ChatMessage()
            message.conversation = conversation
            message.user = user
            message.type = raw_message.type
            message.text = raw_message.text
            message.time = make_aware(datetime.fromtimestamp(raw_message.timestamp))
            message.is_user = True
            message.entities = entities

            self._process(message)

    def accept_inactive(self, conversation_id, user_id, payload, counter):
        with transaction.atomic():
            conversation = ChatConversation.objects.select_for_update().get(pk=conversation_id)
            user = ChatUser.objects.get(pk=user_id)

            # TODO: this might break for more users or with special messages
            if conversation.context_dict != counter:  # user was active
                return

            message = ChatMessage()
            message.conversation = conversation
            message.user = user
            message.type = ChatMessage.SCHEDULE
            message.is_user = True
            message.time = timezone.now()
            message.entities = payload
            self._process(message)

    def accept_scheduled(self, conversation_id, user_id, payload):
        with transaction.atomic():
            conversation = ChatConversation.objects.select_for_update().get(pk=conversation_id)
            if user_id is not None:
                user = ChatUser.objects.get(pk=user_id)
            else:  # generic postback for conversation, not for a specific member
                user = None  # TODO: if there's just one user, set this to the user

            message = ChatMessage()
            message.conversation = conversation
            message.user = user
            message.type = ChatMessage.SCHEDULE
            message.is_user = True
            message.time = timezone.now()
            message.entities = payload
            self._process(message)

    def _process(self, message):
        try:
            logging.info("Processing user message: %s", message)
            processor = MessageProcessor(self, message=message, interceptors=self.interceptors)
            processor.process()
        except Exception as e:
            logging.exception("ERROR: Exception while processing message")
            # TODO: Save error message (ChatMessage.type = ERROR)

        message.conversation.save()
        if message.user is not None:
            message.user.save()
        if self.save_messages:
            message.save()

    def parse_raw_message_entities(self, raw_message):
        entities = raw_message.payload
        if raw_message.text:
            if not entities:
                entities = parse_text_entities(raw_message.text)
            entities['_message_text'] = raw_message.text
        # Remove empty lists
        return {entity: value for entity, value in entities.items() if value is not None and value != []}

    def send(self, conversation, responses, reply_to=None):
        """
        Send responses to a conversation.

        :param conversation: a ChatConversation object
        :param responses: the messages we're sending, Iterable of MessageElement objects
        :param reply_to: (optional) message that we're replying to (used for example in Telegram)
        """
        logging.info("Sending bot responses: %s", responses)
        conversation.interface.send_responses(conversation, reply_to, responses)

        for response in responses:
            message = ChatMessage()
            message.conversation = conversation
            message.user = reply_to.user if reply_to else None
            message.type = ChatMessage.MESSAGE
            message.text = response.get_text()
            message.time = timezone.now()
            message.is_user = False
            message.response_dict = todict(response)
            message.save()

        # Schedule logging messages
        # try:
        #     #sent_time = time.time()
        #     # TODO log bot message
        #     #logging_service.log_bot_message.delay(session=self.session, sent_time=sent_time,
        #     #                                      state=self.current_state_name, response=response)
        # except Exception as e:
        #     print('Error scheduling message log', e)

    def broadcast(self, conversations, responses):
        """
        Send the same responses to multiple conversations.
        Example usage: notifications, news, ...

        :param conversations: Iterable of Conversation objects
        :param responses: Iterable of MessageElement objects
        """
        logging.info("Sending broadcast to %d conversations: %s" % (len(conversations), responses))
        interfaces = {}
        for conversation in conversations:
            a = interfaces.setdefault(conversation.interface, [])
            a.append(conversation)
        for interface, targets in interfaces.items():
            interface.broadcast_responses(targets, responses)

    @staticmethod
    def process_responses(responses):
        if responses is None:
            return []
        if not isinstance(responses, (list, tuple)):
            responses = [responses]
        for i in range(0, len(responses)):
            if isinstance(responses[i], str):
                responses[i] = TextMessage(text=responses[i])
            elif not isinstance(responses[i], MessageElement):
                raise ValueError("Invalid message element of type %s" % type(responses[i]))
        return responses
