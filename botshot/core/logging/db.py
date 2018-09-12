from botshot.core.logging.abs_logger import MessageLogger
from botshot.models import ChatLog, MessageLog
from botshot.core.chat_session import ChatSession
import json
import datetime

class DbLogger(MessageLogger):
    def __init__(self):
        super().__init__()

    def log_user(self, chat_id, session_dict):
        session = ChatSession.from_json(session_dict)
        chat, was_saved = ChatLog.objects.get_or_create(chat_id=session.chat_id, defaults=dict(
            first_name=session.profile.first_name,
            last_name=session.profile.last_name,
            image_url=session.profile.image_url,
            locale=session.profile.locale
        ))

    def _timestamp_to_datetime(self, timestamp: float):
        return datetime.datetime.fromtimestamp(timestamp)

    def log_user_message(self, chat_id, accepted_time: float, state, message_text, message_type, entities):
        time = self._timestamp_to_datetime(accepted_time)
        chat: ChatLog = ChatLog.objects.get(pk=chat_id)
        chat.last_message_time = time
        chat.save()
        message_log = MessageLog()
        message_log.chat = chat
        message_log.text = message_text
        message_log.message_type = message_type
        message_log.is_from_user = True
        message_log.time = time
        message_log.intent = entities.get('intent', [{}])[0].get('value')
        message_log.state = state
        message_log.set_entities(entities)
        message_log.save()

    def log_bot_message(self, chat_id, accepted_time: float, state, message_text, message_type, message_dict: dict):
        chat = ChatLog.objects.get(pk=chat_id)
        message_log = MessageLog()
        message_log.chat = chat
        message_log.text = message_text
        message_log.message_type = message_type
        message_log.is_from_user = False
        message_log.time = self._timestamp_to_datetime(accepted_time)
        message_log.state = state
        message_log.set_response_dict(message_dict)
        message_log.save()
