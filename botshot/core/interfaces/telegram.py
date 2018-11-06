import json
import logging
import random
import string
from datetime import datetime, timedelta
from time import time
from typing import Optional, Generator

import requests
from django.conf import settings

from botshot.core import config
from botshot.core.interfaces import BasicAsyncInterface
from botshot.core.interfaces.adapter.telegram import TelegramAdapter
from botshot.core.parsing.raw_message import RawMessage
from botshot.core.persistence import get_redis
from botshot.models import ChatMessage


class TelegramInterface(BasicAsyncInterface):

    name = 'telegram'
    adapter = TelegramAdapter()
    base_url = 'https://api.telegram.org/bot{}/'.format(config.get_required('TELEGRAM_TOKEN'))

    should_hide_keyboard = config.get('TELEGRAM_HIDE_KEYBOARD', False)

    def on_server_startup(self):
        from django.urls import reverse
        endpoint_url = self.base_url + 'setWebhook'

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
        elif 'callback_query' in request:  # payload button clicked
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
        query_id = callback['id']
        user_id = callback['from']['id']
        chat_instance_id = callback['chat_instance']  # this isn't chat_id
        message = callback.get('message')
        data_key = callback.get('data')  # TODO: sanitize

        if not message:
            logging.warning("Ignoring telegram callback without original message")
            return None

        if not data_key:
            logging.warning("Ignoring telegram callback without data")
            return None

        chat_id = message['chat']['id']
        message_id = message['message_id']
        data = self._retrieve_callback(data_key)
        data = json.loads(data)

        # answer query to hide loading bar in frontend
        url = self.base_url + 'answerCallbackQuery'
        payload = {'callback_query_id': query_id}
        response = requests.post(url, data=payload)
        if not response.json()['ok']:
            logging.error('Error occurred while answering to telegram callback: {}'.format(response.json()))

        # hide keyboard with buttons (not quick replies)
        if self.should_hide_keyboard:
            url = self.base_url + 'editMessageReplyMarkup'
            payload = {'chat_id': chat_id, 'message_id': message_id, 'reply_markup': ''}
            response = requests.post(url, data=payload)
            if not response.json()['ok']:
                logging.error('Error occurred while hiding telegram keyboard: {}'.format(response.json()))

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

    @classmethod
    def _persist_callback(cls, payload) -> str:
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

    @classmethod
    def _retrieve_callback(cls, key) -> Optional[str]:
        redis = get_redis()
        if redis.exists(key):
            return redis.get(key).decode('utf8')
        return None

    def on_message_processing_start(self, message: ChatMessage):
        url = self.base_url + 'sendChatAction'
        payload = {
            'chat_id': message.conversation.raw_conversation_id,
            'action': 'typing'
        }
        response = requests.post(url, data=payload)
        if not response.json()['ok']:
            logging.warning("Error occurred while sending Telegram typing action: {}".format(response.json()))

    def send_responses(self, conversation, reply_to, responses):
        messages = []
        chat_id = conversation.raw_conversation_id
        for response in responses:
            messages += self.adapter.transform_message(response, chat_id)
        for method, payload in messages:
            url = self.base_url + method
            response = requests.post(url, data=payload)
            if not response.json()['ok']:
                logging.warning("Telegram message for method {} failed to send: {}".format(
                    url,
                    response.json())
                )
                break

    def broadcast_responses(self, conversations, responses):
        for conversation in conversations:
            self.send_responses(conversation=conversation, reply_to=None, responses=responses)

    ########################################################################################################################

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
