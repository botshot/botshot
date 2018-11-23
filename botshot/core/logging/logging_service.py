import logging
from typing import List
from botshot.core.logging import MessageLogger
from botshot.core.responses import MessageElement
from botshot.models import ChatMessage
from botshot.tasks import run_async


class AsyncLoggingService(MessageLogger):

    def __init__(self, loggers: List[MessageLogger]):
        self.loggers = loggers

    def log_user_message_start(self, message: ChatMessage, accepted_state):
        self._log_all('log_user_message_start', message=message, accepted_state=accepted_state)

    def log_user_message_end(self, message: ChatMessage, final_state):
        self._log_all('log_user_message_end', message=message, final_state=final_state)

    def log_state_change(self, message: ChatMessage, state):
        self._log_all('log_state_change', message=message, state=state)

    def log_bot_response(self, message: ChatMessage, response: MessageElement, timestamp):
        self._log_all('log_bot_response', message=message, response=response, timestamp=timestamp)

    def log_error(self, message: ChatMessage, state, exception):
        self._log_all('log_error', message=message, state=state, exception=exception)

    def _log_all(self, method_name, **kwargs):
        for logger in self.loggers:
            try:
                run_async(getattr(logger, method_name), **kwargs)
            except:
                logging.error("Logger: {}, Args: {}".format(logger, kwargs))
                logging.exception('Error serializing logging task "{}" for logger "{}"'.format(method_name, logger))
