import json
import logging
from datetime import datetime, timedelta
from typing import Optional

import requests
from django.conf import settings

from botshot.core.interfaces.adapter.microsoft import MicrosoftAdapter
from botshot.core.parsing.message_parser import parse_text_message
from botshot.core.persistence import get_redis
from botshot.tasks import accept_user_message


# FIXME needs to be updated

class MicrosoftInterface():
    name = 'microsoft'
    prefix = 'ms'

    @staticmethod
    def get_base_url(chat_id) -> Optional[str]:
        """
        Loads the correct endpoint url for a chat from redis.
        :param chat_id: Id of the chat.
        :return: url, throws Exception if chat_id not valid or url not found
        """
        if not chat_id:
            raise Exception('Chat id must not be null')
        redis = get_redis()
        url = redis.get('ms_service_url_' + str(chat_id))
        if url is None:
            raise Exception('Service url not found for chat id ' + str(chat_id))

        url = url.decode()
        if not url.endswith('/'):
            url += '/'
        url += 'v3/'
        return url

    @staticmethod
    def set_base_url(chat_id, url):
        if not chat_id or not url:
            raise Exception('Chat id and url must not be null')
        redis = get_redis()
        redis.set('ms_service_url_' + str(chat_id), str(url))

    @staticmethod
    def set_bot_id(chat_id, bot_id):
        """
        Because the microsoft bot api doesn't send the requests to recipient "BOT_ID",
        but to recipient "BOT_ID@nnnn" instead and this ID is required to reply,
        it is saved in redis. When MS updates their documentation about IDs this will hopefully be removed.
        :param chat_id:
        :param bot_id:
        :return:
        """
        if chat_id is None or bot_id is None:
            raise Exception('Chat id and bot id must not be null')
        redis = get_redis()
        redis.set('ms_reply_botid_' + str(chat_id), str(bot_id))

    @staticmethod
    def get_bot_id(chat_id):
        if chat_id is None:
            raise Exception('Chat id must not be null')
        redis = get_redis()
        bot_id = redis.get('ms_reply_botid_' + str(chat_id))
        if bot_id is None:
            raise Exception('Bot ID not found for chat {}'.format(str(chat_id)))
        return bot_id.decode()

    @staticmethod
    def clear():
        pass

    @staticmethod
    def load_profile(uid):
        return {'first_name': 'Tests', 'last_name': ''}

    @staticmethod
    def get_auth_token():
        """
        :returns: Auth token for Microsoft Bot API.
        """
        redis = get_redis()
        if redis.exists('ms_token'):
            return redis.get('ms_token').decode()
        else:
            url = 'https://login.microsoftonline.com/botframework.com/oauth2/v2.0/token'
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            payload = (
                'grant_type=client_credentials' +
                '&client_id=' + settings.BOT_CONFIG.get('MS_BOT_ID') +
                '&client_secret=' + settings.BOT_CONFIG.get('MS_BOT_TOKEN') +
                '&scope=' + 'https://api.botframework.com/.default'
            )
            response = requests.post(url, data=payload, headers=headers)
            if response.status_code != 200:
                logging.error(response.text)
                response.raise_for_status()
            auth_data = response.json()
            token = auth_data['access_token']
            ex = auth_data['expires_in']
            redis.set('ms_token', str(token), ex=ex)
            return token

    @staticmethod
    def post_message(uid, chat_id, response):
        if uid and not chat_id:
            # TODO initiate conversation
            return

        message_id = get_redis().get('chat_message_id:{}'.format(chat_id))
        if message_id:
            message_id = message_id.decode()

        bot_id = MicrosoftInterface.get_bot_id(chat_id)

        payload = {
            "type": "message",
            "from": {
                "id": bot_id
            },
            "conversation": {
                "id": chat_id
            },
            "recipient": {
                "id": uid
            },
            "replyToId": message_id
        }
        payload.update(MicrosoftAdapter(chat_id).to_response(response))

        url = MicrosoftInterface.get_base_url(chat_id) + 'conversations/' + chat_id + '/activities'
        if message_id and False:  # replying to message TODO get and clear atomically or set timeout or something
            url += '/' + message_id
        headers = {
            "Authorization": "Bearer " + MicrosoftInterface.get_auth_token(),
            "Content-Type": "application/json"
        }
        logging.warning(url)
        logging.warning(payload)
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        if response.status_code != 200:
            logging.warning(str(payload))
            logging.warning(response)
            logging.warning(response.text)
        response.raise_for_status()

    @staticmethod
    def send_settings(settings):
        pass

    @staticmethod
    def processing_start(uid, chat_id):
        if not chat_id:
            return
        chat_id = str(chat_id)

        payload = {
            "type": "typing",
            "from": {
                "id": MicrosoftInterface.get_bot_id(chat_id)
            },
            "conversation": {
                "id": chat_id
            }
        }
        url = MicrosoftInterface.get_base_url(chat_id) + 'conversations/' + chat_id + '/activities'
        headers = {"Authorization": "Bearer " + MicrosoftInterface.get_auth_token()}
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        if response.status_code != 200:
            logging.error(response.text)
            response.raise_for_status()

    @staticmethod
    def processing_end(uid, chat_id):
        pass

    @staticmethod
    def state_change(state):
        pass

    @staticmethod
    def has_message_expired(message: dict) -> bool:
        if not (message and 'date' in message):
            logging.warning('Invalid date in message')
            return True
        received = datetime.strptime(message['timestamp'], '%Y-%m-%dT%H:%M:%s.%fZ')
        now = datetime.utcnow()

        if abs(now - received) > timedelta(seconds=settings.BOT_CONFIG.get('MSG_LIMIT_SECONDS')):
            logging.warning('Ignoring message, too old')
            return True
        return False

    @staticmethod
    def accept_request(body, num_tries=1) -> bool:
        if body['type'] == 'message':
            uid = body['from']['id']
            chat_id = body['conversation']['id']
            get_redis().set('chat_message_id:{}'.format(chat_id), body['id'])  # TODO
            MicrosoftInterface.set_base_url(chat_id, body['serviceUrl'])
            MicrosoftInterface.set_bot_id(chat_id, body['recipient']['id'])
            accept_user_message.delay(MicrosoftInterface.name, uid, body, chat_id=chat_id)
            return True
        return False

    @staticmethod
    def parse_message(raw, num_tries=1):
        if 'text' in raw:
            return parse_text_message(raw['text'])
        elif 'value' in raw:
            payload = raw['value']
            payload['_message_text'] = [{'value': None}]
            return {'entities': payload, 'type': 'postback'}
        return {'type': 'undefined'}
