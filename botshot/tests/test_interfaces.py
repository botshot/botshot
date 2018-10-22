import pytest
from django.conf import settings
from django.test import RequestFactory

from botshot.core.interfaces.facebook import FacebookInterface


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
