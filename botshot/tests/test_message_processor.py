import pytest
from mock import Mock
import time

from botshot.core.message_processor import MessageProcessor
from botshot.models import ChatMessage, ChatConversation, ChatUser
from botshot.core.flow import Flow, State


@pytest.fixture
def message():
    message = ChatMessage()
    message.type = ChatMessage.MESSAGE
    message.text = "Hello, world!"
    message.conversation = ChatConversation()
    message.time = time.time()
    message.user = ChatUser()
    message.is_user = True
    message.message_id = 105
    message.entities = {}
    return message


@pytest.fixture
def flows(monkeypatch):
    from botshot.core.flow import Flow, State
    flows = {}
    flows['default'] = Flow("default", intent='default')
    flows['default'].add_state(State(name="root", action=None))
    monkeypatch.setattr("botshot.core.flow.FLOWS", flows)
    return flows


def set_called(dialog):
    dialog.called = True


class TestMessageProcessor():
    
    def test_defaults(self, message, flows, monkeypatch):
        processor = MessageProcessor(message, save_messages=False)
        assert processor.get_flow()
        assert processor.get_flow().name == 'default'
        assert processor.get_state()
        assert processor.get_state().name == 'root'
        assert processor.current_state_name == 'default.root'
    
    def test_unsupported(self, message, flows):
        processor = MessageProcessor(message, save_messages=False)
        flows['greeting'] = Flow("greeting", intent="greeting", unsupported=set_called)
        flows['greeting'].add_state(State("root", action=None))
        message.entities = {}
        processor.current_state_name = "greeting.root"
        processor.process()
        assert hasattr(processor.dialog, 'called')

    def test_state_transition(self, message, flows):
        processor = MessageProcessor(message, save_messages=False)
        flows['default'].add_state(State("transition", action=set_called))
        message.entities['intent'] = [{"value": "greeting"}]
        message.entities['_state'] = [{"value": "default.transition:"}]
        processor.process()
        assert hasattr(processor.dialog, 'called')

    def test_intent_transition(self, message, flows):
        processor = MessageProcessor(message, save_messages=False)
        flows['greeting'] = Flow("greeting", intent="greeting")
        flows['greeting'].add_state(State("root", action=set_called))
        message.entities['intent'] = [{"value": "greeting"}]
        assert processor.current_state_name == "default.root"
        processor.process()
        assert hasattr(processor.dialog, 'called')
        assert processor.current_state_name == "greeting.root"
