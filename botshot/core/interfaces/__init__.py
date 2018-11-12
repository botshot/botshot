from botshot.tasks import run_async
from botshot.models import ChatConversation, ChatUser, ChatMessage
from botshot.core.parsing.raw_message import RawMessage
from botshot.core import config
from django.http.response import HttpResponse, HttpResponseBadRequest
from typing import Generator, Iterable
import json
import logging
import time


class BotshotInterface():
    name = None

    def webhook(self, request):
        raise NotImplementedError()

    def send_responses(self, conversation: ChatConversation, reply_to, responses: Iterable):
        """
        Send responses to a conversation.

        :param conversation: a ChatConversation object
        :param reply_to: (optional) message that we're replying to (used for example in Telegram)
        :param responses: the messages we're sending, Iterable of MessageElement objects
        """
        raise NotImplementedError()

    def broadcast_responses(self, conversations: Iterable[ChatConversation], responses: Iterable):
        """
        Send the same responses to multiple conversations at once.
        Example usage: notifications, news, ...

        :param conversations: Iterable of Conversation objects
        :param responses: Iterable of MessageElement objects
        """
        raise NotImplementedError()

    def fill_conversation_details(self, conversation: ChatConversation):
        pass

    def fill_user_details(self, user: ChatUser):
        pass

    def on_message_processing_start(self, message: ChatMessage):
        pass

    def on_server_startup(self):
        # TODO: run this function at startup
        pass


class BasicAsyncInterface(BotshotInterface):

    def __init__(self):
        self.msg_limit_seconds = config.get('MSG_LIMIT_SECONDS', 15)

    def webhook(self, request):
        from botshot.core.chat_manager import ChatManager
        if request.method == "POST":
            manager = ChatManager()
            request_body = json.loads(request.body.decode('utf-8'))
            raw_messages = self.parse_raw_messages(request_body)
            for raw_message in raw_messages:
                diff_seconds = time.time() - raw_message.timestamp
                if diff_seconds > self.msg_limit_seconds:
                    logging.warning("Delay {} seconds too big, ignoring message!".format(diff_seconds))
                    continue
                self.on_message_received(raw_message)
                logging.info("Received raw message: %s", raw_message)
                run_async(manager.accept, raw_message=raw_message)
            return HttpResponse()

        elif request.method == "GET":
            return self.webhook_get(request)

        return HttpResponseBadRequest()

    def on_message_received(self, raw_message: RawMessage):
        pass

    def webhook_get(self, request):
        pass

    def parse_raw_messages(self, request) -> Generator[RawMessage, None, None]:
        raise NotImplementedError()

    def on_server_startup(self):
        pass

    def broadcast_responses(self, conversations, responses):
        # send one at a time by default, override this for bulk messaging
        for conversation in conversations:
            self.send_responses(conversation=conversation, reply_to=None, responses=responses)
