import logging
import requests
from botshot.core.interfaces.adapter.facebook import FacebookAdapter
from botshot.core.parsing.raw_message import RawMessage
from botshot.core.responses.buttons import *
from botshot.core.responses.responses import *
from botshot.core.responses.settings import ThreadSetting, GreetingSetting, GetStartedSetting, MenuSetting
from django.http.response import HttpResponse
from botshot.core.interfaces import BasicAsyncInterface
from botshot.core import config
from botshot.models import MessageType, ChatMessage, ChatUser


class FacebookInterface(BasicAsyncInterface):
    name = 'facebook'

    def __init__(self):
        super().__init__()
        self.verify_token = config.get_required('FB_VERIFY_TOKEN')
        self.pages = self._init_pages()
        self.adapter = FacebookAdapter()

    def _init_pages(self):
        page_configs = config.get_required('FB_PAGES')
        pages = []
        for page_config in page_configs:
            name = page_config.get('NAME')
            if name is None:
                raise ValueError("FB_PAGES page property 'NAME' is missing.")
            token = page_config.get('TOKEN')
            if token is None:
                raise ValueError("FB_PAGES page '{}' property 'TOKEN' is missing.".format(name))
            page_id = page_config.get('PAGE_ID')
            if page_id is None and len(page_configs) > 1:
                raise ValueError("FB_PAGES page '{}' property 'PAGE_ID' has to be specified "
                                 "when multiple pages are present.".format(name))
            pages.append(MessengerPage(name=name, token=token, page_id=page_id))
        return pages

    def webhook_get(self, request):
        if request.GET.get('hub.verify_token') == self.verify_token:
            return HttpResponse(request.GET['hub.challenge'])
        else:
            return HttpResponse('Error, token not matching FB_VERIFY_TOKEN.')

    def get_page(self, page_id):
        for page in self.pages:
            if page.page_id == page_id or page.page_id is None:
                return page
        raise ValueError("Facebook page not found by page_id = '{}' in FB_PAGES.".format(page_id))

    def parse_raw_messages(self, request):
        # Facebook recommends going through every entry since they might send
        # multiple messages in a single call during high load.
        for entry in request['entry']:
            for event in entry['messaging']:
                raw_message = self._parse_raw_message(event)
                if raw_message is None:
                    continue
                yield raw_message

    def _parse_raw_message(self, event):
        timestamp = event['timestamp']
        user_id = event['sender']['id']
        page_id = event['recipient']['id']
        raw_conversation_id = "{}_{}".format(page_id, user_id)
        conversation_meta = {"page_id": page_id}
        text = None

        if 'postback' in event:
            payload = json.loads(event['postback']['payload'])
            type = MessageType.BUTTON
        elif 'message' in event:
            message = event['message']
            type = MessageType.TEXT
            payload = None
            if 'text' in message:
                text = message['text']
            # Parse payload from special messages
            if 'sticker_id' in message:
                payload = {'sticker_id': message['sticker_id']}
                if message['sticker_id'] in [369239383222810, 369239343222814, 369239263222822]:
                    payload['intent'] = 'thumbs_up'
            elif 'attachments' in message:
                payload = {
                    'current_location': [],
                    'attachment': []
                }
                for attachment in message['attachments']:
                    if 'coordinates' in attachment['payload']:
                        payload['current_location'].append({
                            'value': attachment['title'],
                            'name': attachment['title'],
                            'coordinates': attachment['payload']['coordinates']
                        })
                    if 'url' in attachment['payload']:
                        url = attachment['payload']['url']
                        # TODO: add attachment type by extension
                        payload['attachment'].append({'value': url})
                        payload['intent'] = 'attachment'
            elif 'quick_reply' in message:
                payload = json.loads(message['quick_reply'].get('payload'))
        else:
            logging.warning("Ignoring unrecognized Messenger webhook event: %s", event)
            return None

        return RawMessage(
            interface=self,
            raw_user_id=user_id,
            raw_conversation_id=raw_conversation_id,
            conversation_meta=conversation_meta,
            type=type,
            text=text,
            payload=payload,
            timestamp=timestamp
        )

    def on_message_received(self, raw_message: RawMessage):
        # Confirm accepted message
        self._send_responses(
            fbid=raw_message.raw_user_id,
            conversation_meta=raw_message.conversation_meta,
            responses=[SenderActionMessage('mark_seen')]
        )

    def on_message_processing_start(self, message: ChatMessage):
        # Show typing animation when message processing starts
        self.send_responses(message.user, SenderActionMessage('typing_on'))

    def fill_user_details(self, user: ChatUser):
        try:
            url = "https://graph.facebook.com/v2.6/" + user.raw_user_id
            params = {
                'fields': 'first_name,last_name,profile_pic,picture.type(normal),locale,timezone,gender',
                'access_token': self.get_page(user.conversation.meta.get('page_id')).token
            }
            res = requests.get(url, params=params)
            if not res.status_code == requests.codes.ok:
                logging.error("ERROR: Loading FB profile, got response: {}".format(res.text))
                return

            response = res.json()

            image_url = response.get("picture", {}).get('data', {}).get('url')
            user.save_image(image_url, extension='.jpeg')
            user.first_name = response.get("first_name")
            user.last_name = response.get("last_name")
            user.locale = response.get("locale")
        except:
            logging.error('Unexpected error loading FB user profile')

    def send_responses(self, user: ChatUser, responses):
        self._send_responses(fbid=user.raw_user_id, conversation_meta=user.conversation.meta, responses=responses)

    def _send_responses(self, fbid, conversation_meta, responses):
        page_id = conversation_meta.get('page_id')
        token = self.get_page(page_id).token

        if not isinstance(responses, list):
            responses = [responses]

        for response in responses:
            if isinstance(response, SenderActionMessage):
                request_mode = "messages"
                response_dict = {
                    'sender_action': response.action,
                    'recipient': {"id": fbid},
                }
            elif isinstance(response, MessageElement):
                message_tag = response.get_message_tag()
                message = self.adapter.transform_message(response, conversation_meta=conversation_meta)

                response_dict = {
                    "recipient": {"id": fbid},
                    "message": message,
                    "messaging_type": "MESSAGE_TAG" if message_tag else "RESPONSE",
                    "tag": message_tag,
                }
                request_mode = "messages"
            else:
                raise ValueError('Error: Invalid message type: {}: {}'.format(type(response), response))

            prefix_post_message_url = 'https://graph.facebook.com/v2.6/me/'

            post_message_url = prefix_post_message_url + request_mode + '?access_token=' + token

            r = requests.post(post_message_url,
                              headers={"Content-Type": "application/json"},
                              data=json.dumps(response_dict))

            if r.status_code != 200:
                logging.error('ERROR: MESSAGE REFUSED: {}'.format(response_dict))
                logging.error('ERROR: {}'.format(r.text))
                logging.exception(r.json()['error']['message'])

    # @staticmethod
    # def post_setting(page_id, response):
    #     if isinstance(response, ThreadSetting):
    #         request_mode = "thread_settings"
    #         response_dict = FacebookInterface.to_setting(response)
    #         logging.debug('Sending FB setting: {}'.format(response_dict))
    #         FacebookInterface._do_post(request_mode, response_dict, page_id)
    #     else:
    #         raise ValueError('Error: Invalid message type: {}: {}'.format(type(response), response))


    # @staticmethod
    # def to_setting(response):
    #     if isinstance(response, GreetingSetting):
    #         return {
    #             "greeting": {'text': response.message},
    #             "setting_type": "greeting"
    #         }
    #     elif isinstance(response, GetStartedSetting):
    #         return {
    #             "call_to_actions": [{'payload': json.dumps(response.payload)}],
    #             "setting_type": "call_to_actions",
    #             "thread_state": "new_thread"
    #         }
    #     elif isinstance(response, MenuSetting):
    #         return {
    #             "call_to_actions": [FacebookInterface.to_setting(element) for element in response.elements[:10]],
    #             "setting_type": "call_to_actions",
    #             "thread_state": "existing_thread"
    #         }
    #     elif isinstance(response, MenuElement):
    #         r = {
    #             "title": response.title,
    #             "type": response.type,
    #         }
    #         if response.payload:
    #             r['payload'] = json.dumps(response.payload)
    #         if response.url:
    #             r['url'] = response.url
    #         return r
    #     raise ValueError('Error: Invalid setting type: {}: {}'.format(type(response), response))

    # def upload_attachment(self, conversation, attachment_url, type, is_reusable=True):
    #     """
    #     Uploads a file from the given URL to Facebook's servers.
    #     :returns: Id of the attachment if uploaded successfully, None otherwise.
    #     """
    #
    #     data = {
    #         "message": {
    #             "attachment": {
    #                 "type": type,
    #                 "payload": {
    #                     "is_reusable": is_reusable,
    #                     "url": attachment_url
    #                 }
    #             }
    #         }
    #     }
    #
    #     prefix_post_message_url = 'https://graph.facebook.com/v2.6/me/'
    #     page_id = conversation.meta.get("page_id")
    #     token = self.get_page(page_id).token
    #     post_message_url = prefix_post_message_url + "message_attachments" + '?access_token=' + token
    #     r = requests.post(url=post_message_url, data=json.dumps(data), headers={"Content-Type": "application/json"})
    #     response = r.json()
    #     if r.status_code != 200:
    #         logging.error("Couldn't upload attachment: {}".format(response))
    #         logging.exception(response['error']['message'])
    #     return response.get("attachment_id")


class MessengerPage:
    def __init__(self, name, token, page_id):
        self.name = name
        self.token = token
        self.page_id = page_id