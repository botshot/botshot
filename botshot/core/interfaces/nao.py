import json
import logging
from time import time

from django.http import HttpResponse, HttpResponseBadRequest

from botshot.core import config
from botshot.core.interfaces import BotshotInterface
from botshot.core.parsing.raw_message import RawMessage
from botshot.core.responses import EndSessionResponse, TextMessage
from botshot.models import ChatUser, ChatMessage


class NaoInterface(BotshotInterface):

    name = "nao"
    responses = {}

    def webhook(self, request):
        from botshot.core.chat_manager import ChatManager
        if request.method == "POST":
            manager = ChatManager()
            request_body = json.loads(request.body.decode('utf-8'))
            try:
                raw_message = self.parse_raw_message(request_body)
            except:
                return HttpResponseBadRequest()
            
            logging.info("Received raw message: %s", raw_message)
            self.responses[raw_message.raw_user_id] = []
            manager.accept(raw_message)
            return self._generate_response(raw_message.raw_user_id)

        return HttpResponseBadRequest()

    def parse_raw_message(self, request):
        print(request)
        utterance = request.get('utterance')
        user_id = request.get('user_id')
        timestamp = time()  # int(req_data['timestamp'])

        if not user_id:
            raise Exception()

        message = RawMessage(
            interface=self,
            raw_user_id=user_id,
            raw_conversation_id=user_id,
            conversation_meta={},
            type=ChatMessage.MESSAGE,
            text=utterance,
            payload=None,
            timestamp=timestamp
        )

        return message

    def _generate_response(self, user_id):
        payload = {
            "version": "1.0"
        }
        final_text = []
        end_session = False
        for response in self.responses[user_id]:
            if isinstance(response, EndSessionResponse):
                end_session = True
                break
            elif isinstance(response, TextMessage):
                final_text.append(str(response))
            else:
                logging.warning("Skipping response {} as it's unsupported in Nao".format(response))

        # TODO: what if there are no responses?
        payload = {
            "text": ' '.join(final_text),
            "shouldEndSession": end_session,
        }
        return HttpResponse(content=json.dumps(payload))

    def send_responses(self, conversation, reply_to, responses):
        responses_for_user = self.responses[conversation.raw_conversation_id]
        responses_for_user += responses

    def broadcast_responses(self, conversations, responses):
        raise NotImplementedError()
