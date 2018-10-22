import json
import logging
import string
from datetime import datetime, timedelta
from time import time
from typing import Optional, Generator

import random
import requests
from django.conf import settings

from botshot.core import config
from botshot.core.interfaces import BasicAsyncInterface
from botshot.core.interfaces.adapter.telegram import TelegramAdapter
from botshot.core.parsing.raw_message import RawMessage
from botshot.core.persistence import get_redis
from botshot.models import ChatMessage, ChatUser


class TelegramInterface(BasicAsyncInterface):

    name = 'telegram'
    adapter = TelegramAdapter()

    def base_url(self) -> str:
        token = config.get_required('TELEGRAM_TOKEN')
        return 'https://api.telegram.org/bot{}/'.format(token)

    def on_server_startup(self):
        from django.urls import reverse
        endpoint_url = self.base_url() + 'setWebhook'

        deploy_url = config.get_required(
            'DEPLOY_URL',
            "Telegram requires BOT_CONFIG.DEPLOY_URL to be set in order to register webhooks."
        )
        deploy_url = deploy_url[:-1] if deploy_url[-1] == '/' else deploy_url
        callback_url = deploy_url + reverse('interface_webhook', args=['telegram'])
        logging.info('Reverse telegram URL is: {}'.format(callback_url))

        payload = {'url': callback_url}

        response = requests.post(endpoint_url, data=payload)
        if not response.json()['ok']:
            raise Exception("Error while registering telegram webhook: {}".format(response.json()))

    def parse_raw_messages(self, request) -> Generator[RawMessage, None, None]:
        update_id = request['update_id']  # TODO: use this counter for synchronization
        if 'message' in request:
            yield self._parse_raw_message(request['message'])
        elif 'channel_post' in request:
            yield self._parse_raw_message(request['channel_post'])
        elif 'callback_query' in request:
            yield self._parse_callback_query(request['callback_query'])
        else:
            logging.warning("Ignoring unsupported telegram request")

    def _parse_raw_message(self, message):
        chat_id = message['chat']['id']
        user_id = message.get('from', {}).get('id')  # empty for messages sent to channels
        meta = {}
        date = message['date']
        text = None

        if 'text' in message:
            text = message['text']  # UTF-8, 0-4096 characters
        else:
            logging.warning("Ignoring unsupported telegram message")
            return None

        return RawMessage(
            interface=self,
            raw_user_id=user_id,
            raw_conversation_id=chat_id,
            conversation_meta=meta,
            type=ChatMessage.MESSAGE,
            text=text,
            payload=None,
            timestamp=date
        )

    def _parse_callback_query(self, callback):
        query_id = callback['callback_query_id']
        user_id = callback['user']['id']
        chat_id = callback['chat_instance']  # FIXME: is this correct?
        if 'data' not in callback:
            logging.warning("Ignoring callback without data")
            return None
        data_key = callback['data']  # TODO: sanitize
        data = self._retrieve_callback(data_key)

        # answer query to hide loading bar in frontend
        url = self.base_url() + 'answerCallbackQuery'
        payload = {'callback_query_id': query_id}
        response = requests.post(url, data=payload)
        if not response.json()['ok']:
            logging.error('Error occurred while answering to telegram callback: {}'.format(response.json()))

        # TODO: hide reply keyboard (if needed)

        return RawMessage(
            interface=self,
            raw_user_id=user_id,
            raw_conversation_id=chat_id,
            conversation_meta={},
            type=ChatMessage.BUTTON,
            text=None,
            payload=data,
            timestamp=time()
        )

    def _persist_callback(self, payload) -> str:
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

    def _retrieve_callback(self, key) -> Optional[str]:
        redis = get_redis()
        if redis.exists(key):
            return redis.get(key)
        return None

    def send_responses(self, user: ChatUser, responses):
        raise NotImplementedError()

    def broadcast_responses(self, users, responses):
        raise NotImplementedError()

    ########################################################################################################################

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
                logging.info('Adding message to queue')
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
    #             unfortunately, there is no way to check the age of callback itself
                chat_id = callback_query['message']['chat']['id']
                uid = message['from']['id'] if 'from' in message else None
                accept_user_message.delay(TelegramInterface.name, uid, body, chat_id=chat_id)
                return True
        else:
            logging.warning('Unknown message type')
            return False

    @staticmethod
    def init_webhooks():
        from django.urls import reverse

        base_url = TelegramInterface.get_base_url()
        if not base_url:
            return
        url = base_url + 'setWebhook'

        logging.info('Reverse telegram is: {}'.format(reverse('telegram')))
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
    def post_message(session, response):
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
    def fill_session_profile(session):
        pass
