import json
import time

from botshot.core.chat_session import ChatSession
from botshot.core.logging import MessageLogger


def get_elastic():
    from elasticsearch import Elasticsearch
    from django.conf import settings
    config = settings.BOT_CONFIG.get('ELASTIC')
    if not config:
        return None
    return Elasticsearch(config['HOST'], port=config['PORT'])


class ElasticsearchLogger(MessageLogger):
    def __init__(self):
        super().__init__()
        self.test_id = -1  # FIXME

    def log_user_message(self, dialog, time: float, state, message_text, message_type, entities):
        self._log_message({
            'uid': dialog.session.chat_id,
            'test_id': self.test_id,
            'created': time,
            'is_user': True,
            'text': message_text,
            'state': state,
            'type': message_type,
            'entities': entities
        })

    def log_bot_message(self, dialog, time: float, state, message):
        from botshot.core.responses import TextMessage
        type_ = type(message).__name__ if message else 'TextMessage'
        response = json.loads(
            json.dumps(message, default=lambda obj: obj.__dict__ if hasattr(obj, '__dict__') else str(obj)))

        text = message.text if hasattr(message, 'text') else str(message)

        self._log_message({
            'uid': dialog.session.chat_id,
            'test_id': self.test_id,
            'created': time,
            'is_user': False,
            'text': text,
            'state': state,
            'type': type_,
            'response': response,
        })

    def log_error(self, dialog, state, exception):
        self._log_message({
            'uid': dialog.session.chat_id,
            'test_id' : self.test_id,
            'created': time.time(),
            'is_user': False,
            'text': str(exception),
            'state': state,
            'type': 'error'
        })

    def _log_message(self, message):
        es = get_elastic()
        if not es:
            return
        try:
            print('Logging', message)
            es.index(index="message-log", doc_type='message', body=message)
        except Exception as e:
            print('Unable to log message to Elasticsearch.')
            print(e)
