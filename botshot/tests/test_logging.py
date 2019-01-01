from botshot.core.logging import MessageLogger
from botshot.core.responses import MessageElement
from botshot.models import ChatMessage

from botshot.core.logging.logging_service import AsyncLoggingService


def run_sync(method, _at=None, _seconds=None, **kwargs):
    method(kwargs)
    return None


class TestMessageLogger(MessageLogger):

    def log_user_message_start(self, message: ChatMessage, accepted_state):
        assert message.id == 105

    def log_user_message_end(self, message: ChatMessage, final_state):
        assert message.id == 105

    def log_state_change(self, message: ChatMessage, state):
        assert message.id == 105

    def log_bot_response(self, message: ChatMessage, response: MessageElement, timestamp):
        assert message.id == 105

    def log_error(self, message: ChatMessage, state, exception):
        assert message.id == 105


class LoggingTest:

    def test_logging_service(self, monkeypatch):
        monkeypatch.setattr("botshot.tasks.run_async", run_sync)
        current_state_name = 'default.root'
        message = ChatMessage()
        message.type = ChatMessage.MESSAGE
        message.text = "Hello, world!"
        message.id = 105
        logging_service = AsyncLoggingService([TestMessageLogger()])
        logging_service.log_user_message_start(message, current_state_name)
