import logging

import requests
from django.conf import settings

from botshot.core.logging.abs_logger import MessageLogger
from botshot.core.responses import MessageElement

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

    def log_user_message(self, dialog, accepted_time: float, state, message_text, message_type, entities):
        unsupported = False
        if '_unsupported' in entities and entities['_unsupported']:
            unsupported = entities["_unsupported"][0].get('value', False)
        from django.conf import settings
        payload = {
            "api_key": self.api_key,
            "type": "user",
            "user_id": dialog.session.chat_id,
            "time_stamp": int(accepted_time * 1000),
            "platform": self._interface_to_platform(dialog.session.interface.name),
            "message": message_text,
            "intent": dialog.context.intent.get_value(),
            "session_id": state,
            "not_handled": unsupported,
            "version": settings.BOT_CONFIG.get("VERSION", "1.0")
        }
        response = requests.post(self.base_url + "/message", params=payload)
        if not response.ok:
            logging.error("Chatbase request with code %d, reason: %s", response.status_code, response.reason)
        return response.ok

    def log_bot_message(self, dialog, accepted_time: float, state, message: MessageElement):
        from django.conf import settings
        payload = {
            "api_key": self.api_key,
            "type": "agent",
            "user_id": dialog.session.chat_id,
            "time_stamp": int(accepted_time * 1000),
            "platform": self._interface_to_platform(dialog.session.interface.name),
            "message": str(message),
            "intent": dialog.context.intent.get_value(this_msg=True),
            "session_id": state,
            "not_handled": False,  # only for user messages
            "version": settings.BOT_CONFIG.get("VERSION", "1.0")
        }
        response = requests.post(self.base_url + "/message", params=payload)
        if not response.ok:
            logging.error("Chatbase request with code %d, reason: %s", response.status_code, response.reason)
        return response.ok
