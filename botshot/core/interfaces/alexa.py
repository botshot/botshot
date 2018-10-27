import json
import logging
from time import time

from django.http import HttpResponse, HttpResponseBadRequest

from botshot.core import config
from botshot.core.interfaces import BotshotInterface
from botshot.core.parsing.raw_message import RawMessage
from botshot.models import ChatUser, ChatMessage


class AlexaInterface(BotshotInterface):

    name = "alexa"
    greeting_intent = config.get_required("GREETING_INTENT", 'BOT_CONFIG.GREETING_INTENT is required when using Alexa.')
    responses = {}

    def webhook(self, request):
        from botshot.core.chat_manager import ChatManager
        if request.method == "POST":
            manager = ChatManager()
            request_body = json.loads(request.body.decode('utf-8'))
            raw_message, entities = self.parse_raw_message(request_body)
            logging.info("Received raw message: %s", raw_message)
            self.responses[raw_message.raw_user_id] = []
            manager.accept_with_entities(raw_message, entities)
            return self._generate_response(raw_message.raw_user_id)

        return HttpResponseBadRequest()

    def parse_raw_message(self, request):
        print(request)
        req_data = request['request']
        type = req_data['type']
        user_id = request['session']['user']['userId']
        timestamp = time()  # int(req_data['timestamp'])

        entities = {}

        if type == 'LaunchRequest':
            entities['intent'] = [{"value": self.greeting_intent, "source": self.name, "confidence": 1.0}]
        elif type == 'IntentRequest':
            intent = req_data['intent']['name']
            entities['intent'] = [{"value": intent, "source": self.name, "confidence": 1.0}]
        elif type == 'SessionEndedRequest':
            pass

        message = RawMessage(
            interface=self,
            raw_user_id=user_id,
            raw_conversation_id=user_id,
            conversation_meta={},
            type=ChatMessage.MESSAGE,
            text=None,
            payload=None,
            timestamp=timestamp
        )

        return message, entities

    def _generate_response(self, user_id):
        payload = {
            "version": "1.0"
        }
        for response in self.responses[user_id]:
            payload['response'] = {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": str(response)
                }
            }
            return HttpResponse(content=json.dumps(payload))

    def send_responses(self, conversation, reply_to, responses):
        responses_for_user = self.responses[conversation.raw_conversation_id]
        responses_for_user += responses

    def broadcast_responses(self, conversations, responses):
        raise NotImplementedError()
