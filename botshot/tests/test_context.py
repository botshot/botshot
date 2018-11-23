import time
from unittest import TestCase

from botshot.core.chat_manager import ChatManager

from botshot.models import ChatMessage, ChatConversation, ChatUser

from botshot.core.context import Context
from botshot.core.message_processor import MessageProcessor
from botshot.core.entity_value import EntityValue
from botshot.core.interfaces.test import TestInterface


# mock_redis = mockredis.mock_redis_client()


# def get_fake_redis():
#      return mock_redis


class TestContext(TestCase):

    #@patch('redis.Redis', mockredis.mock_redis_client)
    #@patch('redis.StrictRedis', mockredis.mock_strict_redis_client)
    def setUp(self):
        self.message = ChatMessage()
        self.message.type = ChatMessage.MESSAGE
        self.message.text = "Hello, world!"
        self.message.conversation = ChatConversation()
        self.message.time = time.time()
        self.message.user = ChatUser()
        self.message.is_user = True
        self.message.message_id = 105
        self.dialog = MessageProcessor({}, self.message, ChatManager())

    def test_context_get_set(self):
        context = Context(dialog=self.dialog, entities={}, history=[], counter=0)
        context.intent = "greeting"
        context.intent = "goodbye"
        intent = context.intent.get_value(this_msg=True)
        self.assertEqual(intent, "goodbye")
        cnt = context.intent.count()
        self.assertEqual(cnt, 2)
        self.assertEqual(cnt, len(context.intent))

    def test_context_message_age_filter(self):
        context = Context(dialog=self.dialog, entities={}, history=[], counter=0)
        context.myentity = 1
        context.counter += 1
        context.myentity = 2
        context.counter += 1
        context.myentity = 3
        self.assertTrue('myentity' in context)
        self.assertFalse('myentityy' in context)
        self.assertFalse('myent' in context)
        self.assertEqual(context.counter, 2)
        self.assertEqual(context.myentity.get_value(this_msg=True), 3)
        self.assertEqual(context.myentity.get_value(), 3)
        self.assertEqual(context.myentity.count(), 3)
        self.assertEqual(context.myentity.exactly(messages=1).get_value(), 2)
        self.assertEqual(context.myentity.newer_than(messages=1).count(), 1)
        self.assertEqual(context.myentity.older_than(messages=1).count(), 1)
        self.assertEqual(context.myentity.older_than(messages=1).get_value(), 1)
        self.assertEqual(context.myentity.older_than(messages=0).count(), 2)
        self.assertEqual(context.myentity.newer_than(messages=3).count(), 3)

    def test_set(self):
        context = Context(dialog=self.dialog, entities={}, history=[], counter=0)
        context.myent = "foo"
        context.foo = EntityValue("foo", counter=context.counter, state_set=context.get_state_name(), raw={"value": "foo"})
        self.assertEqual(context.myent.get_value(this_msg=True), "foo")
        self.assertEqual(context.foo.get_value(this_msg=True), "foo")
