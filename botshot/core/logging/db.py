import datetime

from botshot.core.logging.abs_logger import MessageLogger
from botshot.models import ChatLog, MessageLog

from botshot.core.chat_session import ChatSession
from botshot.core.parsing.user_message import UserMessage


class DbLogger(MessageLogger):
    def __init__(self):
        super().__init__()

    def _log_chat(self, session: ChatSession, last_message_time=None):
        chat, created = ChatLog.objects.get_or_create(chat_id=session.chat_id)
        chat.last_message_time = last_message_time
        chat.first_name = session.profile.first_name
        chat.last_name = session.profile.last_name
        chat.locale = session.profile.locale
        if not chat.image and session.profile.tmp_image_url:
            chat.save_image(session.profile.tmp_image_url, extension=session.profile.tmp_image_extension)
        chat.save()

        return chat

    def _timestamp_to_datetime(self, timestamp: float):
        return datetime.datetime.fromtimestamp(timestamp)

    def log_user_message(self, session: ChatSession, state, message: UserMessage, entities: dict):
        time = self._timestamp_to_datetime(message.accepted_time)
        chat = self._log_chat(session, last_message_time=time)

        message_log = MessageLog()
        message_log.chat = chat
        message_log.text = message.text
        message_log.message_type = message.message_type
        message_log.is_from_user = True
        message_log.time = time
        message_log.intent = entities.get('intent', [{}])[0].get('value')
        message_log.state = state
        message_log.set_entities(entities)
        message_log.save()

    def log_bot_message(self, session: ChatSession, sent_time: float, state, response):
        time = self._timestamp_to_datetime(sent_time)
        chat = self._log_chat(session, last_message_time=time)

        message_log = MessageLog()
        message_log.chat = chat
        message_log.text = response.get_text()
        message_log.message_type = type(response).__name__
        message_log.is_from_user = False
        message_log.time = self._timestamp_to_datetime(sent_time)
        message_log.state = state
        message_log.set_response(response)
        message_log.save()
