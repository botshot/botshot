import json
import time

from botshot.core.chat_session import ChatSession
from botshot.core.logging.abs_logger import MessageLogger


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

    def log_user_message(self, dialog, time, state, message, type_, entities):

        entities = entities.copy()
        text = None
        if '_message_text' in entities:
            text = entities['_message_text'][0]['value']
            del (entities['_message_text'])

        message = {
            'uid': dialog.session.chat_id,
            'test_id': self.test_id,
            'created': time,
            'is_user': True,
            'text': text,
            'state': state,
            'type': type_,
            'entities': entities
        }
        self._log_message(message)

    def log_bot_message(self, dialog, time, state, message):
        from botshot.core.responses import TextMessage
        type_ = type(message).__name__ if message else 'TextMessage'
        response = json.loads(
            json.dumps(message, default=lambda obj: obj.__dict__ if hasattr(obj, '__dict__') else str(obj)))

        text = message.text if hasattr(message, 'text') else str(message)

        message = {
            'uid': dialog.session.chat_id,
            'test_id': self.test_id,
            'created': time,
            'is_user': False,
            'text': text,
            'state': state,
            'type': type_,
            'response': response,
        }
        self._log_message(message)

    def log_error(self, dialog, state, exception):
        message = {
            'uid': dialog.chat_id,
            'test_id' : self.test_id,
            'created': time.time(),
            'is_user': False,
            'text': str(exception),
            'state': state,
            'type': 'error'
        }
        self._log_message(message)

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

    def log_user(self, dialog, session: ChatSession):
        user = {
            'uid': session.chat_id,
            'profile': session.profile.to_json() if session.profile else None
        }
        es = get_elastic()
        if not es:
            return
        try:
            es.create(index="message-log", id=user['uid'], doc_type='user', body=user)
        except Exception as e:
            print('Unable to log user profile to Elasticsearch.')
            print(e)
