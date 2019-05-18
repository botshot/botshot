import time

import pytest
from botshot.models import ChatMessage, ChatConversation, ChatUser


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
    monkeypatch.setattr("botshot.core.flow._FLOWS", flows)
    return flows
