import logging
import time

import requests
from django.conf import settings

from botshot.core.logging.abs_logger import MessageLogger


class ChatbaseLogger(MessageLogger):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://chatbase.com/api'
        self.api_key = settings.BOT_CONFIG.get("CHATBASE_API_KEY")
        if self.api_key is None:
            logging.warning("Chatbase API key not provided, will not log!")

    def _interface_to_platform(self, interface: str):
        if interface is None:
            return None
        return interface  # TODO

    def log_user_message(self, session, state, message, entities):
        unsupported = False
        if '_unsupported' in entities and entities['_unsupported']:
            unsupported = entities["_unsupported"][0].get('value', False)

        intent = False
        if 'intent' in entities and entities['intent']:
            unsupported = entities["intent"][0].get('intent', False)

        from django.conf import settings
        payload = {
            "api_key": self.api_key,
            "type": "user",
            "user_id": session.chat_id,
            "time_stamp": int(time.time() * 1000),
            "platform": self._interface_to_platform(session.interface.name),
            "message": message,
            "intent": intent,
            "chat_id": state,
            "not_handled": unsupported,
            "version": settings.BOT_CONFIG.get("VERSION", "1.0")
        }
        response = requests.post(self.base_url + "/message", params=payload)
        if not response.ok:
            logging.error("Chatbase request with code %d, reason: %s", response.status_code, response.reason)
        return response.ok

    def log_bot_message(self, session, sent_time: float, state, response):
        from django.conf import settings
        payload = {
            "api_key": self.api_key,
            "type": "agent",
            "user_id": session.chat_id,
            "time_stamp": int(sent_time * 1000),
            "platform": self._interface_to_platform(session.interface.name),
            "message": str(response),
            "intent": None,
            "chat_id": state,
            "not_handled": False,  # only for user messages
            "version": settings.BOT_CONFIG.get("VERSION", "1.0")
        }
        response = requests.post(self.base_url + "/message", params=payload)
        if not response.ok:
            logging.error("Chatbase request with code %d, reason: %s", response.status_code, response.reason)
        return response.ok
