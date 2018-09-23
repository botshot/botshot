import logging

from botshot.core.responses.responses import TextMessage
from botshot.models import ChatMessage
from botshot.tasks import run_async


class Dialog:

    def __init__(self, message: ChatMessage, context, chat_manager):
        from botshot.core.chat_manager import ChatManager
        from botshot.core.context import Context
        self.message = message
        self.chat_manager = chat_manager  # type: ChatManager
        self.context = context  # type: Context

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
        logging.debug('Scheduling callback %s with payload "%s"', time_formatted, payload)
        return run_async(
            self.chat_manager.accept_delayed,
            at=at,
            seconds=seconds,
            user_id=self.message.user.user_id,
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

        final_responses = []
        for response in responses:
            if isinstance(response, str):
                response = TextMessage(text=response)
            final_responses.append(response)

        self.chat_manager.send(self.message.user, final_responses)
