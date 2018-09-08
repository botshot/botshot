import json
import logging
import string
from datetime import datetime, timedelta
from typing import Optional

import random
import requests
from django.conf import settings

from botshot.core.chat_session import ChatSession
from botshot.core.interfaces.adapter.telegram import TelegramAdapter
from botshot.core.parsing.message_parser import parse_text_message
from botshot.core.persistence import get_redis
from botshot.tasks import accept_user_message


# FIXME needs to be updated

class TelegramInterface:
    name = 'telegram'
    prefix = 'tg'
    adapter = TelegramAdapter()

    @staticmethod
    def get_base_url() -> Optional[str]:
        token = settings.BOT_CONFIG.get('TELEGRAM_TOKEN')
        if not token:
            logging.warning('Telegram token not provided. Telegram will not work.')
            return None
        return 'https://api.telegram.org/bot{}/'.format(token)

    @staticmethod
    def init_webhooks():
        from django.urls import reverse

        base_url = TelegramInterface.get_base_url()
        if not base_url:
            return
        url = base_url + 'setWebhook'

        logging.debug('Reverse telegram is: {}'.format(reverse('telegram')))
        callback_url = settings.BOT_CONFIG.get('DEPLOY_URL') + reverse('telegram')

        payload = {'url': callback_url}
        response = requests.post(url, data=payload)
        if not response.json()['ok']:
            logging.warning(response.json())


    @staticmethod
    def clear():
        pass

    @staticmethod
    def load_profile(uid):
        return {'first_name': 'Tests', 'last_name': ''}

    @staticmethod
    def post_message(session: ChatSession, response):
        from botshot.core.interfaces.adapter.telegram import TelegramAdapter
        base_url = TelegramInterface.get_base_url()
        if not base_url:
            return
        adapter = TelegramAdapter()
        adapter.prepare_message(response, session)
        messages = adapter.transform_message(response, session)
        for method, payload in messages:
            url = base_url + method
            response = requests.post(url, data=payload)
            if not response.json()['ok']:
                logging.error('Telegram request failed!')
                logging.error(response.json())
                logging.error('for method {}'.format(method))
                logging.error('message is:')
                logging.error(payload)
                return

    @staticmethod
    def answer_callback_query(query_id, chat_id, message_id):
        base_url = TelegramInterface.get_base_url()
        if not base_url:
            return
        url = base_url + 'answerCallbackQuery'
        payload = {
            'callback_query_id': str(query_id)
        }
        response = requests.post(url, data=payload)
        if not response.json()['ok']:
            logging.error('Unable to answer callback query')
            logging.error(response.json())
        # hide reply keyboard after clicking
        url = base_url + 'editMessageReplyMarkup'
        payload = {'chat_id': chat_id, 'message_id': message_id, 'reply_markup': ''}
        response = requests.post(url, data=payload)
        if not response.json()['ok']:
            logging.error('Unable to remove quick replies')
            logging.error(response.json())

    @staticmethod
    def send_settings(settings):
        pass

    @staticmethod
    def processing_start(session):
        base_url = TelegramInterface.get_base_url()
        if not base_url:
            return
        url = base_url + 'sendChatAction'
        payload = {
            'chat_id': session.meta['chat_id'],
            'action': 'typing'
        }
        response = requests.post(url, data=payload)
        if not response.json()['ok']:
            logging.warning(response.json())

    @staticmethod
    def processing_end(session):
        pass

    @staticmethod
    def state_change(state):
        pass

    @staticmethod
    def has_message_expired(message: dict) -> bool:
        if not (message and 'date' in message):
            logging.warning('Invalid date in message')
            return True
        received = datetime.fromtimestamp(int(message['date']))
        now = datetime.utcnow()

        if abs(now - received) > timedelta(seconds=settings.BOT_CONFIG['MSG_LIMIT_SECONDS']):
            logging.warning('Ignoring message, too old')
            return True
        return False

    @staticmethod
    def accept_request(body, num_tries=1) -> bool:
        if not body or 'update_id' not in body:
            logging.warning('Invalid message received: {}'.format(body))
            return False

        if 'message' in body:
            message = body['message']

            chat_id = message['chat']['id']
            uid = message['from']['id'] if 'from' in message else None  # null for group chats
            if uid and not TelegramInterface.has_message_expired(message):
                logging.debug('Adding message to queue')
                meta = {"chat_id": chat_id, "uid": uid}
                session = ChatSession(TelegramInterface, str(chat_id), meta=meta)
                TelegramInterface.fill_session_profile(session)
                accept_user_message.delay(session, body)
                return True
            else:
                logging.warning('No sender specified, ignoring message')
                return False
        elif 'callback_query' in body:
            callback_query = body['callback_query']
            query_id = callback_query['id']
            message = callback_query['message']
            if message:
                chat_id = message['chat']['id']
                message_id = message['message_id']
                TelegramInterface.answer_callback_query(query_id, chat_id, message_id)
            else:
                logging.error('No message in callback query, probably too old, ignoring.')
            if 'message' in callback_query:
                # unfortunately, there is no way to check the age of callback itself
                chat_id = callback_query['message']['chat']['id']
                uid = message['from']['id'] if 'from' in message else None
                accept_user_message.delay(TelegramInterface.name, uid, body, chat_id=chat_id)
                return True
        else:
            logging.warning('Unknown message type')
            return False

    @staticmethod
    def parse_message(raw, num_tries=1):
        if 'message' in raw and 'text' in raw['message']:
            return parse_text_message(raw['message']['text'])
        elif 'callback_query' in raw:
            callback_query = raw['callback_query']
            data = TelegramInterface.retrieve_callback(callback_query.get('data'))
            if data:
                payload = json.loads(data)
                return {'entities': payload, 'type': 'postback'}
        return {'type': 'undefined'}

    @staticmethod
    def persist_callback(payload) -> str:
        """
        Persists payload to be used with Telegram callbacks (which can be max. 64B)
        and returns a string that can be used to retrieve the payload from redis.
        The payload will be persisted for a week.
        :param  payload     Payload to be persisted in Redis.
        :return             Unique string associated with the payload, which can be sent to Telegram.
        """
        redis = get_redis()
        key = ''.join(random.choice(string.hexdigits) for i in range(63))
        while redis.exists(key):
            key = ''.join(random.choice(string.hexdigits) for i in range(63))
        redis.set(key, payload, ex=3600 * 24 * 7)
        return key

    @staticmethod
    def retrieve_callback(key) -> Optional[str]:
        redis = get_redis()
        if redis.exists(key):
            return redis.get(key)
        return None

    @staticmethod
    def fill_session_profile(session):
        pass
