from abc import ABC, abstractmethod


class MessageLogger(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def log_user_message(self, dialog, time, state, message, type_, entities):
        pass

    @abstractmethod
    def log_bot_message(self, dialog, time, state, message):
        pass

    def log_error(self, dialog, state, exception):
        pass

    def log_user(self, dialog, chat_session):
        pass
