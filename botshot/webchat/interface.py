import logging
from botshot.core.chat_session import ChatSession, Profile
from botshot.core.parsing.message_parser import parse_text_message
from botshot.core.parsing.user_message import UserMessage
import uuid
import random
import time

class WebchatInterface:
    name = 'webchat'
    prefix = 'web'

    def __init__(self, webchat_id):
        self.webchat_id = webchat_id

    def get_unique_id(self):
        return self.webchat_id

    def load_profile(self):
        return Profile()

    def post_message(self, response):
        pass

    def send_settings(self, settings):
        pass

    def processing_start(self):
        pass

    def processing_end(self):
        pass

    def state_change(self, state_name):
        pass

    def parse_message(self, raw_message) -> UserMessage:
        text = raw_message['text']
        if raw_message.get("payload"):
            return UserMessage('postback', text=text, payload=raw_message['payload'])
        return parse_text_message(text)

    @staticmethod
    def make_webchat_id() -> str:
        return uuid.uuid4().hex

    @staticmethod
    def make_random_name(min_sylables, max_sylables) -> str:
        length = random.randint(min_sylables, max_sylables) * 2
        return ''.join([(random.choice('aeiouy') if i % 2 else random.choice('bcdfghjklmnpqrstvwxz')) for i in range(0, length)]).capitalize()
