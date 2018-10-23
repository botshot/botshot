from time import time

import pytest
from django.conf import settings
from django.test import RequestFactory

from botshot.core.interfaces.alexa import AlexaInterface
from botshot.core.interfaces.facebook import FacebookInterface
from botshot.core.interfaces.telegram import TelegramInterface
from botshot.models import ChatMessage


class TestFacebookInterface():

    verify_token = 'hello_world'
    challenge = 'a challenging string'
    page = {"NAME": "TEST", "TOKEN": "TEST", "PAGE_ID": "TEST"}
    req_factory = RequestFactory()

    @pytest.fixture
    def interface(self):
        settings.BOT_CONFIG['FB_VERIFY_TOKEN'] = self.verify_token
        settings.BOT_CONFIG['FB_PAGES'] = [self.page]
        yield FacebookInterface()
        del settings.BOT_CONFIG['FB_VERIFY_TOKEN']
        del settings.BOT_CONFIG['FB_PAGES']

    def message_template(self, sender=10, recipient=11):
        return {
            "object": "page",
            "entry": [{
                    "id": self.page['PAGE_ID'],
                    "time": 0,
                    "messaging": [{
                            "sender": {"id": sender},
                            "recipient": {"id": recipient},
                    }]
                }]
        }

    def test_verify_webhook(self, interface):
        data = {
            'hub.mode': 'subscribe',
            'hub.verify_token': self.verify_token,
            'hub.challenge': self.challenge,
        }
        req = self.req_factory.get('', data=data)
        retval = interface.webhook_get(req)
        assert retval.content.decode('utf8') == self.challenge

    def test_message_received(self, interface):
        # interface.webhook_get()
        data = self.message_template()
        message = {
            "mid": "mid.1457764197618:41d102a3e1ae206a38",
            "text": "hello, world!",
            "quick_reply": {
                "payload": "<DEVELOPER_DEFINED_PAYLOAD>"
            }
        }
        data['entry'][0]['messaging'][0]['message'] = message
        req = self.req_factory.post('', data=data)
        retval = interface.webhook(req)
        assert retval.status_code == 200


class TestTelegramInterface():

    token = '000000000:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'
    message = {
        "update_id": 673009215,
        "message": {
            "message_id":1,
            "from":{"id":1,"is_bot":False,"first_name":"Matus","last_name":"Zilinec","language_code":"en-US"},
            "chat":{"id":1,"first_name":"Matus","last_name":"Zilinec","type":"private"},
            "date": time(),
            "text":"hello"
        }
    }

    @pytest.fixture
    def interface(self):
        settings.BOT_CONFIG['TELEGRAM_TOKEN'] = self.token
        interface = TelegramInterface()
        # interface.on_server_startup()
        yield interface
        del settings.BOT_CONFIG['TELEGRAM_TOKEN']

    def test_message_received(self, interface):
        messages = interface.parse_raw_messages(self.message)
        message = next(messages)
        assert message.type == ChatMessage.MESSAGE
        assert message.text == self.message['message']['text']

    def test_postback_received(self, interface):
        # TODO
        pass


class TestAlexaInterface():

    request = {
        "version": "1.0",
        "session": {},
        "request": {
            "type": "LaunchRequest",
            "requestId": "request.id.string",
            "timestamp": "string"
        }
    }

    @pytest.fixture
    def interface(self):
        yield AlexaInterface()

    def test_message_received(self, interface):
        req = self.request.copy()
