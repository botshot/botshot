from unittest import TestCase

from botshot.core.chat_session import ChatSession
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
        self.session = ChatSession(TestInterface, 'test_id')
        self.dialog = MessageProcessor(self.session)

    def test_context_get_set(self):
        context = Context(dialog=self.dialog, entities={}, history=[], counter=0)
        context.intent = "greeting"
        context.intent = "goodbye"
        intent = context.intent.get_value(this_msg=True)
        self.assertEquals(intent, "goodbye")
        cnt = context.intent.count()
        self.assertEquals(cnt, 2)
        self.assertEquals(cnt, len(context.intent))

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
        self.assertEquals(context.counter, 2)
        self.assertEquals(context.myentity.get_value(this_msg=True), 3)
        self.assertEquals(context.myentity.get_value(), 3)
        self.assertEquals(context.myentity.count(), 3)
        self.assertEquals(context.myentity.exactly(messages=1).get_value(), 2)
        self.assertEquals(context.myentity.newer_than(messages=1).count(), 1)
        self.assertEquals(context.myentity.older_than(messages=1).count(), 1)
        self.assertEquals(context.myentity.older_than(messages=1).get_value(), 1)
        self.assertEquals(context.myentity.older_than(messages=0).count(), 2)
        self.assertEquals(context.myentity.newer_than(messages=3).count(), 3)

    def test_set(self):
        context = Context(dialog=self.dialog, entities={}, history=[], counter=0)
        context.myent = "foo"
        context.foo = EntityValue("foo", counter=context.counter, state_set=context.get_state_name(), raw={"value": "foo"})
        self.assertEqual(context.myent.get_value(this_msg=True), "foo")
        self.assertEqual(context.foo.get_value(this_msg=True), "foo")
