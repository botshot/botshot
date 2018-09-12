import json
import logging

import random

from botshot.core.chat_session import ChatSession
from botshot.core.parsing.message_parser import parse_text_message
from botshot.tasks import accept_user_message


# class WebchatInterface:
#     name = 'webchat'
#     prefix = 'web'
#     messages = []
#     states = []
#
#     @staticmethod
#     def clear():
#         WebchatInterface.messages = []
#         WebchatInterface.states = []
#
#     @staticmethod
#     def load_profile(uid):
#         return {'first_name': 'Tests', 'last_name': ''}
#
#     @staticmethod
#     def post_message(session, response):
#         uid = session.meta.get("uid")
#         #data = json.dumps(response.to_response())
#
#         WebMessageData.objects.create(uid=uid, is_response=True, data=data)
#
#     @staticmethod
#     def send_settings(settings):
#         pass
#
#     @staticmethod
#     def processing_start(session):
#         pass
#
#     @staticmethod
#     def processing_end(session):
#         pass
#
#     @staticmethod
#     def state_change(state):
#         if not WebchatInterface.states or WebchatInterface.states[-1] != state:
#             WebchatInterface.states.append(state)
#
#     @staticmethod
#     def parse_message(user_message, num_tries=1):
#         logging.info('[WEBCHAT] @ parse_message')
#         if user_message.get('text'):
#             return parse_text_message(user_message.get('text'))
#         elif user_message.get("payload"):
#             # data = json.loads(user_message["payload"])
#             data = user_message['payload']
#             # data = json.loads(b64decode(user_message["payload"]).decode())
#             logging.info("Payload is: {}".format(data))
#             if isinstance(data, dict):
#                 return {'entities': data, 'type': 'postback'}
#             else:
#                 from botshot.core.serialize import json_deserialize
#                 payload = json.loads(data, object_hook=json_deserialize)
#                 payload['_message_text'] = [{'value': None}]
#                 return {'entities': payload, 'type': 'postback'}
#
#     @staticmethod
#     def accept_request(msg: WebMessageData):
#         uid = str(msg.uid)
#
#         logging.info('[WEBCHAT] Received message from {}'.format(uid))
#         session = ChatSession(WebchatInterface, uid, meta={"uid": uid})
#         accept_user_message.delay(session.to_json(), {"text": msg.message().get('text')})
#
#     @staticmethod
#     def accept_postback(msg: WebMessageData, data):
#         uid = str(msg.uid)
#         data = json.loads(data)
#
#         logging.info('[WEBCHAT] Received postback from {}'.format(uid))
#         session = ChatSession(WebchatInterface, uid, meta={"uid": uid})
#         accept_user_message.delay(session.to_json(), {"_message_text": msg.message().get('text'), "payload": data})
#
#     @staticmethod
#     def make_uid(username) -> str:
#         uid = None
#         tries = 0
#         while (not uid or len(WebMessageData.objects.filter(uid__exact=uid)) != 0) or tries < 100:
#             uid = '_'.join([str(username), str(random.randint(1000, 99999))])
#             tries += 1
#         # delete messages for old session with this uid, if there was one
#         # FIXME invalidate the previous user's session!
#         try:
#             WebMessageData.objects.get(uid__exact=uid).delete()
#         except Exception:
#             pass  # first user, there is no such table yet
#         return uid
#
#     @staticmethod
#     def destroy_uid(uid):
#         WebMessageData.objects.filter(uid__exact=uid).delete()
