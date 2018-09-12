from abc import ABC, abstractmethod
from botshot.core.responses import MessageElement

class MessageLogger(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def log_user_message(self, chat_id, accepted_time: float, state, message_text, message_type, entities):
        pass

    @abstractmethod
    def log_bot_message(self, chat_id, accepted_time: float, state, message_text, message_type, message_dict):
        pass

    def log_error(self, chat_id, state, exception):
        pass

    def log_user(self, chat_id, session_dict):
        pass
