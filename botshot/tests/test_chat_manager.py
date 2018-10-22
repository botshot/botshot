from time import time
from typing import Generator

import pytest

from botshot.core.chat_manager import ChatManager
from botshot.core.interfaces import BasicAsyncInterface
from botshot.core.parsing.raw_message import RawMessage
from botshot.models import ChatUser, ChatConversation


class TestInterface(BasicAsyncInterface):

    name = "test"

    def parse_raw_messages(self, request) -> Generator[RawMessage, None, None]:
        pass

    def send_responses(self, user: ChatUser, responses):
        pass

    def broadcast_responses(self, users, responses):
        pass


@pytest.fixture
def chat_mgr():
    yield ChatManager()


@pytest.mark.django_db
def test_accept(chat_mgr):
    chat_id = 'chat_id'
    message = RawMessage(
        interface=TestInterface(),
        raw_user_id="foo",
        raw_conversation_id=chat_id,
        conversation_meta={},
        type="message",
        text="Hello world!",
        payload=None,
        timestamp=time()
    )
    chat_mgr.accept(message)

    model = ChatConversation.objects.get(
        raw_conversation_id=chat_id,
        interface_name="test"
    )

    assert model is not None
