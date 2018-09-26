from abc import ABC, abstractmethod

from botshot.core.responses import MessageElement
from botshot.models import ChatMessage


class MessageLogger(ABC):

    @abstractmethod
    def log_user_message_start(self, message: ChatMessage, accepted_state):
        pass

    @abstractmethod
    def log_user_message_end(self, message: ChatMessage, final_state):
        pass

    @abstractmethod
    def log_state_change(self, message: ChatMessage, state):
        pass

    @abstractmethod
    def log_bot_response(self, message: ChatMessage, response: MessageElement, timestamp):
        pass

    @abstractmethod
    def log_error(self, message: ChatMessage, state, exception):
        pass

