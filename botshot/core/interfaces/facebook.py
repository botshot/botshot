import datetime
import logging

import requests
from django.conf import settings

from botshot.core.chat_session import ChatSession
from botshot.core.interfaces.adapter.facebook import FacebookAdapter
from botshot.core.parsing.message_parser import parse_text_message
from botshot.core.persistence import get_redis
from botshot.core.responses.buttons import *
from botshot.core.responses.responses import *
from botshot.core.responses.settings import ThreadSetting, GreetingSetting, GetStartedSetting, MenuSetting
from botshot.tasks import accept_user_message
from botshot.core.chat_session import Profile
from django.http.response import HttpResponse

class FacebookInterface():
    name = 'facebook'
    prefix = 'fb'
    TEXT_LENGTH_LIMIT = 320
    adapter = FacebookAdapter()

    def get_request(self, request):
        if request.GET.get('hub.verify_token') == settings.BOT_CONFIG.get('FB_VERIFY_TOKEN'):
            return HttpResponse(request.GET['hub.challenge'])
        else:
            return HttpResponse('Error, invalid token')

    # Post function to handle Facebook messages
    def post_request(self, request):
        # Converts the text payload into a python dictionary
        request_body = json.loads(request.body.decode('utf-8'))
        FacebookInterface.accept_request(request_body)
        return HttpResponse()

    # Post function to handle Facebook messages
    @staticmethod
    def accept_request(request):
        # Facebook recommends going through every entry since they might send
        # multiple messages in a single call during high load.
        for entry in request['entry']:
            for raw_message in entry['messaging']:
                ts_datetime = datetime.datetime.fromtimestamp(int(raw_message['timestamp']) / 1000)
                crr_datetime = datetime.datetime.utcnow()
                diff = crr_datetime - ts_datetime
                if diff.total_seconds() > settings.BOT_CONFIG.get('MSG_LIMIT_SECONDS', 15):
                    logging.warning("Delay {} too big, ignoring message!".format(diff))
                    continue

                FacebookInterface._accept_message(entry, raw_message)

    @staticmethod
    def _accept_message(entry, raw_message):
        # get and persist user and page ids
        logging.debug('Incoming raw FB message: {}'.format(raw_message))
        user_id = raw_message['sender']['id']
        page_id = entry['id']
        meta = {"user_id": user_id, "page_id": page_id}
        page_user_id = "{}_{}".format(page_id, user_id)
        profile = FacebookInterface.load_profile(user_id, page_id)
        session = ChatSession(FacebookInterface, unique_id=page_user_id, meta=meta, profile=profile)
        # Confirm accepted message
        FacebookInterface.post_message(session, SenderActionMessage('mark_seen'))
        # Add it to the message queue
        accept_user_message.delay(session, raw_message)

    @staticmethod
    def get_page_token(page_id):
        if 'FB_PAGE_TOKENS' in settings.BOT_CONFIG:
            tokens = settings.BOT_CONFIG.get('FB_PAGE_TOKENS')
            if page_id not in tokens:
                raise Exception('Page id "{}" not in tokens: {}'.format(page_id, tokens))
            return tokens.get(page_id)
        elif 'FB_PAGE_TOKEN' in settings.BOT_CONFIG:  # there is just one page
            return settings.BOT_CONFIG.get("FB_PAGE_TOKEN")
        return None

    @staticmethod
    def load_profile(user_id, page_id, cache=True):

        db = get_redis()
        key = 'fb_profile_{}_{}'.format(page_id, user_id)

        if not cache or not db.exists(key):
            logging.debug('Loading fb profile...')

            try:
                url = "https://graph.facebook.com/v2.6/" + user_id
                params = {
                    'fields': 'first_name,last_name,profile_pic,picture.type(normal),locale,timezone,gender',
                    'access_token': FacebookInterface.get_page_token(page_id)
                }
                res = requests.get(url, params=params)
                if not res.status_code == requests.codes.ok:
                    logging.error("ERROR loading FB profile! Response: {}".format(res.text))
                    return {}

                response = res.json()
            except Exception as e:
                print('Error loading user profile:', e)
                return None
            db.set(key, json.dumps(response), ex=3600 * 24 * 14)  # save value, expire in 14 days
        else:
            response = json.loads(db.get(key).decode('utf-8'))

        image_url = response.get("picture", {}).get('data', {}).get('url')
        profile = Profile(
            first_name=response.get("first_name"),
            last_name=response.get("last_name"),
            tmp_image_url=image_url,
            tmp_image_extension='.jpeg',
            locale=response.get("locale")
        )
        return profile

    @staticmethod
    def fill_session_profile(session: ChatSession):
        if not session:
            raise ValueError("Session is None")
        user_id, page_id = session.meta.get("user_id"), session.meta.get("page_id")
        profile_dict = FacebookInterface.load_profile(user_id, page_id)
        session.profile.first_name = profile_dict.get("first_name")
        session.profile.last_name = profile_dict.get("last_name")
        return session

    @staticmethod
    def post_message(session: ChatSession, response):
        fbid = session.meta.get("user_id")
        page_id = session.meta.get("page_id")

        if isinstance(response, SenderActionMessage):
            request_mode = "messages"
            response_dict = {
                'sender_action': response.action,
                'recipient': {"id": fbid},
            }
        elif isinstance(response, MessageElement):
            message_tag = response.get_message_tag()
            message = FacebookInterface.to_message(response, session)
            response_dict = {
                "recipient": {"id": fbid},
                "message": message,
                "messaging_type": "MESSAGE_TAG" if message_tag else "RESPONSE",
                "tag": message_tag,
            }
            request_mode = "messages"
        else:
            raise ValueError('Error: Invalid message type: {}: {}'.format(type(response), response))

        FacebookInterface._do_post(request_mode, response_dict, page_id)

    @staticmethod
    def post_setting(page_id, response):
        if isinstance(response, ThreadSetting):
            request_mode = "thread_settings"
            response_dict = FacebookInterface.to_setting(response)
            logging.debug('Sending FB setting: {}'.format(response_dict))
            FacebookInterface._do_post(request_mode, response_dict, page_id)
        else:
            raise ValueError('Error: Invalid message type: {}: {}'.format(type(response), response))

    @staticmethod
    def _do_post(request_mode, response_dict, page_id):
        prefix_post_message_url = 'https://graph.facebook.com/v2.6/me/'
        token = FacebookInterface.get_page_token(page_id)
        post_message_url = prefix_post_message_url + request_mode + '?access_token=' + token

        r = requests.post(post_message_url,
                          headers={"Content-Type": "application/json"},
                          data=json.dumps(response_dict))
        if r.status_code != 200:
            logging.error('ERROR: MESSAGE REFUSED: {}'.format(response_dict))
            logging.error('ERROR: {}'.format(r.text))
            logging.exception(r.json()['error']['message'])

    @staticmethod
    def to_setting(response):
        if isinstance(response, GreetingSetting):
            return {
                "greeting": {'text': response.message},
                "setting_type": "greeting"
            }
        elif isinstance(response, GetStartedSetting):
            return {
                "call_to_actions": [{'payload': json.dumps(response.payload)}],
                "setting_type": "call_to_actions",
                "thread_state": "new_thread"
            }
        elif isinstance(response, MenuSetting):
            return {
                "call_to_actions": [FacebookInterface.to_setting(element) for element in response.elements[:10]],
                "setting_type": "call_to_actions",
                "thread_state": "existing_thread"
            }
        elif isinstance(response, MenuElement):
            r = {
                "title": response.title,
                "type": response.type,
            }
            if response.payload:
                r['payload'] = json.dumps(response.payload)
            if response.url:
                r['url'] = response.url
            return r
        raise ValueError('Error: Invalid setting type: {}: {}'.format(type(response), response))

    @staticmethod
    def to_message(response, session):
        FacebookInterface.adapter.prepare_message(response, session)
        return FacebookInterface.adapter.transform_message(response)
        # if isinstance(response, TextMessage):
        #     if response.buttons:
        #         return {
        #             "attachment": {
        #                 "type": "template",
        #                 "payload": {
        #                     "template_type": "button",
        #                     "text": response.text[:FacebookInterface.TEXT_LENGTH_LIMIT],
        #                     "buttons": [FacebookInterface.to_message(button) for button in response.buttons]
        #                 }
        #             }
        #         }
        #     message = {'text': response.text[:FacebookInterface.TEXT_LENGTH_LIMIT]}
        #     if response.quick_replies:
        #         message["quick_replies"] = [FacebookInterface.to_message(reply) for reply in response.quick_replies]
        #     return message
        #
        # elif isinstance(response, GenericTemplateMessage):
        #     return {
        #         "attachment": {
        #             "type": "template",
        #             "payload": {
        #                 "template_type": "generic",
        #                 "elements": [FacebookInterface.to_message(element) for element in response.elements[:10]]
        #             }
        #         }
        #     }
        #
        # elif isinstance(response, AttachmentMessage):
        #     return {
        #         "attachment": {
        #             "type": response.attachment_type,
        #             "payload": {
        #                 "url": response.url
        #             }
        #         }
        #     }
        #
        # elif isinstance(response, GenericTemplateElement):
        #     message = {
        #         "title": response.title,
        #         "image_url": response.image_url,
        #         "subtitle": response.subtitle,
        #         "item_url": response.item_url
        #     }
        #     if response.buttons:
        #         message["buttons"] = [FacebookInterface.to_message(button) for button in response.buttons]
        #     return message
        #
        # elif isinstance(response, QuickReply):
        #     return response.to_response()
        #
        # elif isinstance(response, Button):
        #     return response.to_response()
        #
        # elif isinstance(response, ListTemplate):
        #     return response.to_response()
        #
        # raise ValueError('Error: Invalid message type: {}: {}'.format(type(response), response))

    @staticmethod
    def send_settings(setting_list):
        for setting in setting_list:
            if 'FB_PAGE_TOKENS' in settings.BOT_CONFIG:
                for page_id in settings.BOT_CONFIG.get('FB_PAGE_TOKENS'):
                    FacebookInterface.post_setting(page_id, setting)
            elif 'FB_PAGE_TOKEN' in settings.BOT_CONFIG:
                FacebookInterface.post_setting("", setting)

    @staticmethod
    def processing_start(session: ChatSession):
        # Show typing animation
        FacebookInterface.post_message(session, SenderActionMessage('typing_on'))

    @staticmethod
    def processing_end(session: ChatSession):
        pass

    @staticmethod
    def state_change(state):
        pass

    @staticmethod
    def parse_message(raw_message, num_tries=1):
        if 'postback' in raw_message:
            payload = json.loads(raw_message['postback']['payload'])
            return {'entities': payload, 'type': 'postback'}
        elif 'message' in raw_message:
            if 'sticker_id' in raw_message['message']:
                return FacebookInterface.parse_sticker(raw_message['message']['sticker_id'])
            if 'attachments' in raw_message['message']:
                attachments = raw_message['message']['attachments']
                return FacebookInterface.parse_attachments(attachments)
            if 'quick_reply' in raw_message['message']:
                payload = json.loads(raw_message['message']['quick_reply'].get('payload'))
                if payload:
                    return {'entities': payload, 'type': 'postback'}
            if 'text' in raw_message['message']:
                return parse_text_message(raw_message['message']['text'])
        return {'type': 'undefined'}

    @staticmethod
    def parse_sticker(sticker_id):
        if sticker_id in [369239383222810, 369239343222814, 369239263222822]:
            return {'entities': {'emoji': 'thumbs_up_sign'}, 'type': 'message'}

        return {'entities': {'sticker_id': sticker_id}, 'type': 'message'}

    @staticmethod
    def parse_attachments(attachments):
        entities = {
            'intent': [],
            'current_location': [],
            'attachment': []
        }
        for attachment in attachments:
            if 'coordinates' in attachment['payload']:
                coordinates = attachment['payload']['coordinates']
                entities['current_location'].append({'value': attachment['title'], 'name': attachment['title'],
                                                     'coordinates': coordinates, 'timestamp': datetime.datetime.now()})
            if 'url' in attachment['payload']:
                url = attachment['payload']['url']
                # TODO: add attachment type by extension
                entities['attachment'].append({'value': url})
                entities['intent'].append({'value': 'attachment'})
        return {'entities': entities, 'type': 'message'}

    @staticmethod
    def upload_attachment(session, attachment_url, type, is_reusable=True):
        """
        Uploads a file from the given URL to Facebook's servers.
        :returns: Id of the attachment if uploaded successfully, None otherwise.
        """

        data = {
            "message": {
                "attachment": {
                    "type": type,
                    "payload": {
                        "is_reusable": is_reusable,
                        "url": attachment_url
                    }
                }
            }
        }

        prefix_post_message_url = 'https://graph.facebook.com/v2.6/me/'
        page_id = session.meta.get("page_id")
        token = FacebookInterface.get_page_token(page_id)
        post_message_url = prefix_post_message_url + "message_attachments" + '?access_token=' + token
        r = requests.post(url=post_message_url, data=json.dumps(data), headers={"Content-Type": "application/json"})
        response = r.json()
        if r.status_code != 200:
            logging.error("Couldn't upload attachment: {}".format(response))
            logging.exception(response['error']['message'])
        return response.get("attachment_id")
