import time
import pytest

from botshot.core.chat_manager import ChatManager

from botshot.models import ChatMessage, ChatConversation, ChatUser

from botshot.core.context import Context
from botshot.core.message_processor import MessageProcessor
from botshot.core.entity_value import EntityValue
from botshot.core.interfaces.test import TestInterface
from botshot.core.tests import MockDialog


# mock_redis = mockredis.mock_redis_client()


# def get_fake_redis():
#      return mock_redis

@pytest.mark.django_db
class TestContext():

    #@patch('redis.Redis', mockredis.mock_redis_client)
    #@patch('redis.StrictRedis', mockredis.mock_strict_redis_client)
    def setUp(self, monkeypatch):
        self.message = ChatMessage()
        self.message.type = ChatMessage.MESSAGE
        self.message.text = "Hello, world!"
        self.message.conversation = ChatConversation()
        self.message.time = time.time()
        self.message.user = ChatUser()
        self.message.is_user = True
        self.message.message_id = 105
        self.dialog = MessageProcessor(chat_manager=None, message=self.message)

    def test_context_get_set(self):
        dialog = MockDialog()
        context = Context(entities={}, history=[], counter=0)
        context.intent = "greeting"
        context.intent = "goodbye"
        intent = context.intent.get_value(this_msg=True)
        assert intent == "goodbye"
        cnt = context.intent.count()
        assert cnt == 2
        assert cnt == len(context.intent)

    def test_context_message_age_filter(self):
        context = Context(entities={}, history=[], counter=0)
        context.myentity = 1
        context.counter += 1
        context.myentity = 2
        context.counter += 1
        context.myentity = 3
        assert 'myentity' in context
        assert 'myentityy' not in context
        assert 'myent' not in context
        assert context.counter == 2
        assert context.myentity.get_value(this_msg=True) == 3
        assert context.myentity.get_value() == 3
        assert context.myentity.count() == 3
        assert context.myentity.exactly(messages=1).get_value() == 2
        assert context.myentity.newer_than(messages=1).count() == 1
        assert context.myentity.older_than(messages=1).count() == 1
        assert context.myentity.older_than(messages=1).get_value() == 1
        assert context.myentity.older_than(messages=0).count() == 2
        assert context.myentity.newer_than(messages=3).count() == 3

    def test_set(self):
        context = Context(entities={}, history=[], counter=0)
        context.myent = "foo"
        context.foo = EntityValue("foo", counter=context.counter, state_set=context.get_state_name(), raw={"value": "foo"})
        assert context.myent.get_value(this_msg=True) == "foo"
        assert context.foo.get_value(this_msg=True) == "foo"

    def test_history(self):
        states = ["first", "second", "third", "fourth", "fifth"]
        context = Context(entities={}, history=[], counter=0, history_limit=10)
        for i, state in enumerate(states):
            context.add_state(state)
            assert context.get_state_name() == state
            assert context.counter == i + 1
        for i, state in enumerate(reversed(states)):
            assert context.get_history_state(i)['name'] == state
