from botshot.core.dialog_manager import DialogManager
from botshot.core.parsing.raw_message import RawMessage
from botshot.models import ChatConversation, ChatUser, ChatMessage, MessageType
from botshot.core.flow import FLOWS
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from botshot.core.parsing.message_parser import parse_text_entities
import logging

class MessageManager:

    def process(self, raw_message: RawMessage):
        entities = self.parse_raw_message_entities(raw_message)

        with transaction.atomic():
            try:
                conversation: ChatConversation = ChatConversation.objects.select_for_update().get(
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
                conversation = ChatConversation.objects.select_for_update().get(pk=conversation.conversation_id)

            conversation.last_message_time = timezone.now()

            try:
                user = conversation.users.get(raw_user_id=raw_message.raw_user_id)
            except ObjectDoesNotExist:
                user = ChatUser()
                user.conversation = conversation
                user.raw_user_id = raw_message.raw_user_id
                # Save user before filling details so that image field can be saved
                user.save()
                # TODO: also update details of existing users every once in a while
                raw_message.interface.fill_user_details(user)
                user.save()

            message = ChatMessage()
            message.user = user
            message.type = raw_message.type
            message.text = raw_message.text
            # FIXME !!!!!!!!!!!!!!!!!!
            # FIXME !!!!!!!!!!!!!!!!!!
            # FIXME !!!!!!!!!!!!!!!!!!
            # FIXME use raw_message.timestamp
            message.time = timezone.now()
            message.is_user = True
            message.entities = entities

            self.run_dialog(message)

    def process_delayed(self, user_id, callback_state):
        with transaction.atomic():
            user: ChatUser = ChatUser.objects.select_for_update().select_related('conversation').get(pk=user_id)
            message = ChatMessage()
            message.user = user
            message.type = MessageType.SCHEDULE
            message.is_user = True
            message.time = timezone.now()
            message.entities = {
                '_state': callback_state
            }

            self.run_dialog(message)

    def run_dialog(self, message):
        try:
            dialog = DialogManager(flows=FLOWS, message=message, message_manager=self)
            dialog.run()
        except Exception as e:
            logging.exception("ERROR: Error encountered while running message actions")
            # TODO log error using log service
            #from botshot.core.logging import logging_service
            #logging_service.log_error(session=session, exception=e, state=dialog.current_state_name)

        # Should propagate to save sender, conversation and context
        # messages will be saved at all times and possibly erased after a time period or using max total messages limit
        # TODO: Create configuration option to save user only
        message.save()

    def parse_raw_message_entities(self, raw_message):
        entities = raw_message.payload
        if raw_message.text:
            if not entities:
                entities = parse_text_entities(raw_message.text)
            entities['_message_text'] = raw_message.text
        # Remove empty lists
        return {entity: value for entity, value in entities.items() if value is not None and value != []}


# @shared_task
# def accept_inactivity_callback(session, context_counter, callback_state, inactive_seconds):
#     from botshot.core.dialog_manager import DialogManager
#     dialog = DialogManager(session)
#
#     # User has sent a message, cancel inactivity callback
#     if dialog.context.counter != context_counter:
#         print('Canceling inactivity callback after user message.')
#         return
#
#     message = UserMessage('schedule', payload={
#         '_inactive_seconds': inactive_seconds,
#         '_state': callback_state
#     })
#
#     _process_message(dialog, session, message)


# TODO: Make scheduled callbacks work again
# def setup_schedule_callbacks(sender, callback):
#     callbacks = settings.BOT_CONFIG.get('SCHEDULE_CALLBACKS')
#     if not callbacks:
#         return
#
#     for name in callbacks:
#         params = callbacks[name]
#         print('Scheduling task {}: {}'.format(name, params))
#         if isinstance(params, dict):
#             cron = crontab(**params)
#         elif isinstance(params, int):
#             cron = params
#         else:
#             raise Exception(
#                 'Specify either number of seconds or dict of celery crontab params (hour, minute): {}'.format(params))
#         sender.add_periodic_task(
#             cron,
#             callback.s(name),
#         )
#         print(' Scheduled for {}'.format(cron))