import importlib
import logging
import os
import random
import time
import traceback

from django.conf import settings
from django.utils.module_loading import import_string

from botshot.core.parsing.message_parser import parse_text_entities
from botshot.core.persistence import get_redis
from botshot.core.responses import CarouselTemplate
from botshot.core.responses.buttons import *
from botshot.core.responses.responses import *
from .interfaces.test import TestInterface


class ConversationTestException(Exception):
    def __init__(self, message):
        super(ConversationTestException, self).__init__(message)

class UserMessage:
    def get_parsed(self):
        pass

class UserTextMessage(UserMessage):
    def __init__(self, text):
        self.text = text
        self.entities = {}

    def produces_entity(self, entity, value = None):
        self.entities[entity] = value
        return self

    def get_parsed(self):
        TestLog.log('Sending user message "{}".'.format(self.text))
        entities = parse_text_entities(self.text)

        for entity, values in entities.items():
            TestLog.log('- Entity {}: {}'.format(entity, values))

        for entity in self.entities:
            expected_value = self.entities[entity]
            if entity not in entities:
                raise ConversationTestException('- Expected entity "{}" not extracted from message "{}".'.format(entity, self.text))
            elif expected_value:
                value = entities[entity][0]['value']
                if expected_value != value:
                    raise ConversationTestException('- Extracted "{}" instead of "{}" in entity "{}" from message "{}".'.format(value, expected_value, entity, self.text))
                TestLog.log('- Extracted expected value "{}" of entity "{}".'.format(value, entity))
            else:
                TestLog.log('- Extracted expected entity "{}".'.format(entity))

        return entities

class UserPostbackMessage(UserMessage):
    def __init__(self, payload):
        self.payload = payload

    def get_parsed(self):
        TestLog.log('Sending user postback: {}.'.format(self.payload))
        return {'entities': self.payload, 'type':'postback'}


class UserButtonMessage(UserMessage):
    def __init__(self, title):
        self.title = title


class BotMessage():
    def __init__(self, klass):
        self.klass = klass
        self.text = None
        self.can_be_repeated = False

    def with_text(self, text):
        self.text = text
        return self

    def repeated(self):
        self.can_be_repeated = True
        return self

    def check(self, message):
        TestLog.log('Checking message: {}'.format(message))
        
        if message is None:
            raise ConversationTestException('- Expected message type {} but no message returned by bot.'.format(self.klass.__name__))
        if not isinstance(message, self.klass):
            raise ConversationTestException('- Expected message type {} but received {} from bot: "{}".'.format(self.klass.__name__, type(message).__name__, message))
        
        TestLog.log('- Checking received {} from bot: "{}".'.format(self.klass.__name__, message))

        if self.text:
            if not isinstance(message, TextMessage):
                raise ConversationTestException('- Only text messages can be checked for text content, but received {}.'.format(type(message)))
            if self.text != message.text:
                raise ConversationTestException('- Expected text content "{}" but received "{}"'.format(self.text, message.text))
    
            TestLog.log('- Received expected message text "{}" from bot.'.format(self.text))

        return True

class StateChange():
    def __init__(self, name):
        self.name = name

    def check(self, state):
        TestLog.log('Checking state: {}'.format(state))
        if state is None:
            raise ConversationTestException('Expected new state {} but no state change occurred.'.format(self.name))
        if self.name != state:
            raise ConversationTestException('Expected new state {} but moved to {}.'.format(self.name, state))

        TestLog.log('Moved to expected new state {}.'.format(self.name))
        return True



class ConversationTest:
    def __init__(self, name, actions, benchmark=False):
        self.benchmark = benchmark
        self.chat_id = 'benchmark_'+str(random.randint(1, 10000000)) if benchmark else 'test'
        self.name = name
        self.actions = actions
        self.session = ChatSession(unique_id=self.chat_id, interface=TestInterface, is_logged=not self.benchmark, is_test=True)

    def run(self):
        self.init()
        stats = []
        for action in self.actions:
            stat = self.run_action(action)
            if stat:
                stats.append(stat)
        
        report = {'min':{'total':0}, 'max':{'total':0}, 'avg':{'total':0}}
        for key in ['init','parsing','processing']:
            report['min'][key] = min([s[key] for s in stats])
            report['avg'][key] = sum([s[key] for s in stats]) / len(stats)
            report['max'][key] = max([s[key] for s in stats])
            report['min']['total'] += report['min'][key]
            report['avg']['total'] += report['avg'][key]
            report['max']['total'] += report['max'][key]
        return report

    def init(self):
        self.buttons = {}
        from .message_processor import MessageProcessor
        MessageProcessor.clear_chat(self.session.chat_id)
        TestLog.clear()
        TestInterface.clear()
        

    def run_action(self, action):
        
        if isinstance(action, UserButtonMessage):
            payload = self.buttons.get(action.title, {}).get('payload')
            if not payload:
                raise ConversationTestException('Wanted to press button {}, but it is not present.'.format(action.title))
            action = UserPostbackMessage(payload)

        if isinstance(action, UserMessage):
            from .message_processor import MessageProcessor
            start_time = time.time() # test_id=self.name, use_logging=not self.benchmark
            dialog = MessageProcessor(session=self.session)
            time_init = time.time() - start_time
            start_time = time.time()
            entities = action.get_parsed()
            time_parsing = time.time() - start_time
            start_time = time.time()
            dialog.process(parsed['type'], parsed['entities'])
            time_processing = time.time() - start_time
            return {'init':time_init, 'parsing':time_parsing, 'processing':time_processing}

        if isinstance(action, BotMessage):
            message = TestInterface.messages.pop(0) if TestInterface.messages else None
            action.check(message)
            if action.can_be_repeated:
                while TestInterface.messages:
                    peek = TestInterface.messages[0]
                    try:
                        action.check(peek)
                        print('Message matches repeatable message, popping: {}'.format(peek))
                        message = TestInterface.messages.pop(0)
                    except:
                        break
            buttons = []
            if isinstance(message, TextMessage):
                buttons = message.buttons
                buttons += message.quick_replies
            if isinstance(message, CarouselTemplate):
                for element in message.elements:
                    buttons += element.buttons
            for button_qr in buttons:
                if hasattr(button_qr, 'payload') and button_qr.payload:
                    button_qr.payload['_log_text'] = button_qr.title
                print('Adding button {}'.format(button_qr.title))
                self.buttons[button_qr.title] = {'payload':getattr(button_qr, 'payload', None), 'url': getattr(button_qr, 'url', None)}

        if isinstance(action, StateChange):
            state = TestInterface.states.pop(0) if TestInterface.states else None
            action.check(state)

        return None



class ConversationTestRecorder:

    @staticmethod
    def record_user_message(message_type, message):
        logging.warning('Recording user {}: {}'.format(message_type, message))
        db = get_redis()
        db.lpush('test_actions', json.dumps({'type':'user', 'body':{'type':message_type,'entities':message}}, default=json_serialize))

    @staticmethod
    def record_bot_message(message):
        record = {'type':type(message).__name__}
        if isinstance(message, TextMessage):
            record['text'] = message.text
        logging.warning('Recording bot message: {}'.format(record))
        db = get_redis()
        db.lpush('test_actions', json.dumps({'type':'bot', 'body':record}))

    @staticmethod
    def record_state_change(state):
        logging.warning('Recording state change: {}'.format(state))
        db = get_redis()
        db.lpush('test_actions', json.dumps({'type':'state', 'body':state}))

    @staticmethod
    def record_start():
        logging.warning('Starting recording')
        db = get_redis()
        db.delete('test_actions')
        message = TextMessage(text="Starting to record ;)")\
            .add_button(PayloadButton(title="Stop recording", payload={"test_record": "stop"}))
        return message

    @staticmethod
    def record_stop():
        logging.warning('Stopping recording')
        deploy_url = settings.BOT_CONFIG.get('DEPLOY_URL', "localhost:8000")
        message = TextMessage("Done recording ;)")\
            .add_button(LinkButton(title='Get result', url=deploy_url + '/botshot/test_record'))\
            .add_button(PayloadButton(title='Start again', payload={"test_record": "start"}))
        return [message]

    @staticmethod
    def get_result():
        db = get_redis()
        actions = db.lrange('test_actions', 0, -1)
        response = """from botshot.core.responses import *
from botshot.core.tests import *

actions = []
"""
        state = None
        for action in actions[::-1]:
            action = json.loads(action.decode('utf-8'), object_hook=json_deserialize)
            body = action['body']
            print('Action body: {}'.format(body))
            if action['type'] == 'user':
                if body['type'] == 'message':
                    text_entity = body['entities']['_message_text'][0]
                    text = text_entity['value']
                    message = 'UserTextMessage("{}")'.format(text)
                    for entity in body['entities']:
                        if entity.startswith('_'):
                            continue
                        value = body['entities'][entity][0].get('value')
                        if isinstance(value, str):
                            message += '.produces_entity("{}","{}")'.format(entity, value)
                        else:
                            message += '.produces_entity("{}")'.format(entity)
                if body['type'] == 'postback':
                    text_entity = body['entities'].get('_message_text')[0]
                    text = text_entity['value']
                    message = 'UserButtonMessage("{}")'.format(text)
                response += "\n\n"+'actions.append({})'.format(message) + "\n"
            elif action['type'] == 'bot':
                message = 'BotMessage({})'.format(body['type'])
                if 'text' in body:
                    message += '.with_text("{}")'.format(body['text'])
                response += 'actions.append({})'.format(message)
            elif action['type'] == 'state':
                if body == state:
                    continue
                response += 'actions.append(StateChange("{}"))'.format(body)
                state = body
            response += "\n"

        return response
        
        
class TestLog:
    messages = []

    @staticmethod
    def clear():
        TestLog.messages = []

    @staticmethod
    def log(message):
        print(message)
        TestLog.messages.append(message)

    @staticmethod
    def get():
        return TestLog.messages


def _get_test_modules():
    path = settings.BOT_CONFIG.get("TEST_MODULE", 'tests')
    path = path.replace('.', '/')
    print("Loading tests from directory: ", path)
    files = filter(lambda f: os.path.join(path, f).endswith('.py') and not f.startswith('_'), os.listdir(path))
    return sorted([f.replace('.py','') for f in files])


def _run_test_module(name, benchmark=False):

    path = settings.BOT_CONFIG.get("TEST_MODULE", 'tests')

    module = importlib.import_module("." + name, package=path)
    importlib.reload(module)

    result = _run_test_actions(name, module.actions, benchmark=benchmark)
    test = {'name': name, 'result': result}
    db = get_redis()
    db.hset('test_results', name, json.dumps(test))
    return test


def _run_test_actions(name, actions, benchmark=False):
    test = ConversationTest(name, actions, benchmark=benchmark)
    start_time = time.time()
    report = None
    try:
      report = test.run()
    except Exception as e:
      log = TestLog.get()
      fatal = not isinstance(e, ConversationTestException)
      if fatal:
        trace = traceback.format_exc()
        print(trace)
        log.append(trace)
      return {'status': 'exception' if fatal else 'failed', 'log':log, 'message':str(e), 'report':report}

    elapsed_time = time.time() - start_time
    return {'status': 'passed', 'log':TestLog.get(), 'duration':elapsed_time, 'report':report}
