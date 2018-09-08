from abc import ABC, abstractmethod
from botshot.core.responses import MessageElement

class MessageLogger(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def log_user_message(self, session, state, message, entities):
        pass

    @abstractmethod
    def log_bot_message(self, session, sent_time: float, state, response):
        pass

    def log_error(self, session, state, exception):
        pass

