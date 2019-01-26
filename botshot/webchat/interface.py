import json
import logging
import random
import time
import uuid

from botshot.core.chat_manager import ChatManager
from botshot.core.interfaces import BotshotInterface
from botshot.core.parsing.raw_message import RawMessage
from botshot.models import ChatMessage
from botshot.tasks import run_async


class WebchatInterface(BotshotInterface):

    name = 'webchat'

    def webhook(self, request):
        manager = ChatManager()
        
        text = request.POST.get('message')
        payload = None
        if request.POST.get('payload'):
            payload = json.loads(request.POST.get('payload'))

        if not text and not payload:
            logging.warning("[Webchat] Neither text nor payload was provided")
            return False

        webchat_id = request.session["webchat_id"]
        msg_type = ChatMessage.BUTTON if payload else ChatMessage.MESSAGE

        raw_message = RawMessage(
            interface=self,
            raw_user_id=webchat_id,
            raw_conversation_id=webchat_id,
            conversation_meta={},
            type=msg_type,
            text=text,
            payload=payload,
            timestamp=time.time()
        )

        self.on_message_received(raw_message)
        logging.info("[Webchat] Received raw message: %s", raw_message)
        run_async(manager.accept, raw_message=raw_message)
        return True

    def on_message_received(self, raw_message):
        pass

    def send_responses(self, conversation, reply_to, responses):
        pass

    def broadcast_responses(self, conversations, responses):
        pass

    @staticmethod
    def make_webchat_id() -> str:
        return uuid.uuid4().hex

    @staticmethod
    def make_random_name(min_sylables, max_sylables) -> str:
        length = random.randint(min_sylables, max_sylables) * 2
        return ''.join([(random.choice('aeiouy') if i % 2 else random.choice('bcdfghjklmnpqrstvwxz')) for i in range(0, length)]).capitalize()
