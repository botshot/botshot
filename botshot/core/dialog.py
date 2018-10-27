import logging
import time

from botshot.core.logging.logging_service import AsyncLoggingService
from botshot.core.responses.responses import TextMessage
from botshot.models import ChatMessage, ChatConversation, ChatUser
from botshot.tasks import run_async


class Dialog:

    def __init__(self, message: ChatMessage, context, chat_manager, logging_service: AsyncLoggingService):
        from botshot.core.chat_manager import ChatManager
        from botshot.core.context import Context
        self.message = message
        self.sender = self.message.user  # type: ChatUser
        self.conversation = self.message.conversation  # type: ChatConversation
        self.chat_manager = chat_manager  # type: ChatManager
        self.context = context  # type: Context
        self.logging_service = logging_service

    def inactive(self, payload, seconds=None):
        logging.warning("dialog.inactive is not implemented yet!")

    def schedule(self, payload, at=None, seconds=None):
        """
        Schedules a state transition in the future.
        :param payload:  Payload to send in the scheduled message.
        :param at:       A datetime with timezone
        :param seconds:  An integer, seconds from now
        """
        if not at and not seconds:
            raise ValueError('Specify either "at" or "seconds" parameter')
        time_formatted = "at {}".format(at) if at else "in {} seconds".format(seconds)
        logging.info('Scheduling callback %s with payload "%s"', time_formatted, payload)
        return run_async(
            self.chat_manager.accept_scheduled,
            _at=at,
            _seconds=seconds,
            reply_to=self.message.message_id,
            payload=payload
        )

    def send(self, responses):
        """
        Send one or more messages to the user.
        :param responses:       Instance of MessageElement, str or Iterable.
        """

        if responses is None:
            return

        if not (isinstance(responses, list) or isinstance(responses, tuple)):
            responses = [responses]

        for i in range(0, len(responses)):
            if isinstance(responses[i], str):
                responses[i] = TextMessage(text=responses[i])

        self.chat_manager.send(self.message.conversation, self.message, responses)

        for response in responses:
            self.logging_service.log_bot_response(self.message, response, timestamp=time.time())
