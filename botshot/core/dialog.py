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
        if not seconds or seconds < 0:
            raise ValueError('Specify a positive "seconds" parameter')
        time_formatted = "in {} seconds".format(seconds)
        logging.info('Setting inactivity callback %s with payload "%s"', time_formatted, payload)
        task_id = run_async(
            self.chat_manager.accept_inactive,
            _at=None,
            _seconds=seconds,
            conversation_id=self.conversation.id,
            user_id=self.sender.user_id,
            payload=payload,
            counter=self.context.counter
        )
        return task_id

    def schedule(self, payload, at=None, seconds=None):
        """
        Schedules a state transition in the future.
        :param payload:  Payload to send in the scheduled message.
        :param at:       A datetime with timezone
        :param seconds:  An integer, seconds from now
        """
        if not at and (not seconds or seconds < 0):
            raise ValueError('Specify either "at" or a positive "seconds" parameter')
        time_formatted = "at {}".format(at) if at else "in {} seconds".format(seconds)
        logging.info('Scheduling callback %s with payload "%s"', time_formatted, payload)
        task_id = run_async(
            self.chat_manager.accept_scheduled,
            _at=at,
            _seconds=seconds,
            # reply_to=self.message.message_id,
            conversation_id=self.conversation.id,
            user_id=self.sender.user_id,
            payload=payload
        )
        return task_id

    def send(self, responses):
        """
        Send one or more messages to the user.
        :param responses:       Instance of MessageElement, str or Iterable.
        """

        responses = self.chat_manager.process_responses(responses)
        self.chat_manager.send(self.message.conversation, self.message, responses)

        for response in responses:
            self.logging_service.log_bot_response(self.message, response, timestamp=time.time())
