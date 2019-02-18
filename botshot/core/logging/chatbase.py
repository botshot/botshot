import logging
import time

import requests
from django.conf import settings

from botshot.core import config
from botshot.core.logging import MessageLogger
from botshot.core.responses import MessageElement
from botshot.models import ChatMessage
import calendar


class ChatbaseLogger(MessageLogger):

    def __init__(self):
        super().__init__()
        self.base_url = 'https://chatbase.com/api'
        self.api_key = settings.BOT_CONFIG.get("CHATBASE_API_KEY")
        self.bot_version = config.get("VERSION", 'no version')
        if self.api_key is None:
            logging.warning("Chatbase API key not provided, will not log!")

    def _interface_to_platform(self, interface: str):
        if interface is None:
            return None
        return interface  # TODO

    def log_user_message_end(self, message: ChatMessage, final_state):

        intent = None
        if message.entities.get('intent'):
            intent_entity = message.entities["intent"]
            if isinstance(intent_entity, list):
                intent_entity = intent_entity[0]
            intent = intent_entity.get('value') if isinstance(intent_entity, dict) else str(intent_entity)

        payload = {
            "api_key": self.api_key,
            "type": "user",
            "user_id": message.conversation.id,
            "time_stamp": int(calendar.timegm(message.time.utctimetuple()) * 1000),
            "platform": self._interface_to_platform(message.conversation.interface_name),
            "message": self._message_description(message),
            "intent": intent,  # docs: don't set if it's a generic catch-all intent
            "not_handled": not message.supported,
            "version": self.bot_version
        }
        # TODO: add session_id attribute
        logging.debug("Sending to chatbase: {}".format(payload))
        response = requests.post(self.base_url + "/message", params=payload)
        if not response.ok:
            logging.error("Chatbase request with code %d, reason: %s", response.status_code, response.reason)
        return response.ok

    def log_bot_response(self, message: ChatMessage, response: MessageElement, timestamp):
        payload = {
            "api_key": self.api_key,
            "type": "agent",
            "user_id": message.conversation.id,
            "time_stamp": int(timestamp * 1000),
            "platform": self._interface_to_platform(message.conversation.interface_name),
            "message": response.get_text() or str(message),  # docs: the raw message body regardless of type
            "intent": None,
            "not_handled": False,  # only for user messages
            "version": self.bot_version
        }
        logging.debug("Sending to chatbase: {}".format(payload))
        response = requests.post(self.base_url + "/message", params=payload)
        if not response.ok:
            logging.error("Chatbase request with code %d, reason: %s", response.status_code, response.reason)
        return response.ok

    def log_user_message_start(self, message: ChatMessage, accepted_state):
        pass

    def log_state_change(self, message: ChatMessage, state):
        pass

    def log_error(self, message: ChatMessage, state, exception):
        pass

    def _message_description(self, message):
        if message.type == ChatMessage.MESSAGE:
            return message.text
        elif message.type == ChatMessage.BUTTON:
            return "(button): " + str(message.text or "")
        else:
            return "(event): " + str(message.text or "")
