from botshot.core.interfaces.adapter.message_adapter import MessageAdapter
from botshot.core.responses import *


class FacebookAdapter(MessageAdapter):

    def __init__(self):
        super().__init__()

        self.functions = {
            TextMessage: self._text_message,

            # Buttons
            LinkButton: self._link_button,
            PayloadButton: self._payload_button,
            PhoneButton: self._phone_button,
            ShareButton: self._share_button,
            AccountLinkButton: self._account_link_button,
            AccountUnlinkButton: self._account_unlink_button,

            # Quick replies
            QuickReply: self._quick_reply,
            LocationQuickReply: self._location_quick_reply,

            # Templates
            CardTemplate: self._card_template,
            ListTemplate: self._list_template,
            CarouselTemplate: self._carousel_template,

            # Media
            AttachmentMessage: self._attachment_message,
            MediaMessage: self._media_message,
        }

    def _share_button(self, button):
        return {'type': 'element_share'}

    def _account_unlink_button(self, button):
        return {'type': 'account_unlink'}

    def _location_quick_reply(self, button):
        return {'content_type': 'location'}

    def transform_message(self, message: MessageElement, conversation_meta=None):
        if isinstance(message, MediaMessage):
            # FIXME: media messages upload
            raise NotImplementedError("Media messages are not supported yet.")
            #if not self._is_facebook_url(message) and not self._retrieve_attachment(message.url):
            #    self._upload_attachment(conversation, message.url, message.media_type, message.allow_cache)
        message_type = type(message)
        fn = self.functions.get(message_type)
        if not fn:
            raise Exception("Response {} is not supported in Facebook Messenger at the moment!".format(message_type))
        return fn(message)


    def _is_facebook_url(self, url):
        """Used to check whether an attachment needs to be uploaded to Facebook before sending."""
        return False  # FIXME

    def _upload_attachment(self, conversation, url, type, allow_cache):
        """Uploads an attachment to FB servers."""
        from botshot.core.persistence import get_redis
        from botshot.core.interfaces.facebook import FacebookInterface

        redis = get_redis()
        att_id = FacebookInterface.upload_attachment(conversation, url, type, allow_cache)
        if att_id is not None:
            expiry = 60 * 60 * 24  # a day
            redis.set("FB_ATTACHMENT_FOR_{url}".format(url=url), att_id, ex=expiry)

    def _retrieve_attachment(self, url):
        """Retrieves an attachment ID from FB servers."""
        from botshot.core.persistence import get_redis

        redis = get_redis()
        att_id = redis.get("FB_ATTACHMENT_FOR_{url}".format(url=url))
        return att_id.decode("utf8") if att_id else None

    def _text_message(self, message: TextMessage):
        if len(message.buttons) and message.quick_replies:
            raise Exception("A message can only have one of: quick replies, buttons")
        elif len(message.buttons):
            return {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": message.text,
                        "buttons": [self.transform_message(button) for button in message.buttons]
                    }
                }
            }
        else:
            response = {'text': message.text}
            if message.quick_replies:
                response["quick_replies"] = [self.transform_message(reply) for reply in message.quick_replies]
            return response

    def _link_button(self, button: LinkButton):
        return {
            'title': button.title,
            'type': 'web_url',
            'url': button.url,
            'webview_height_ratio': button.webview_height_ratio
        }

    def _payload_button(self, button: PayloadButton):
        return {
            'title': button.title,
            'type': 'postback',
            'payload': json.dumps(button.payload)
        }

    def _phone_button(self, button: PhoneButton):
        return {
            'title': button.title,
            'type': 'phone_number',
            'payload': button.phone_number
        }

    def _account_link_button(self, button: AccountLinkButton):
        return {
            'type': 'account_link',
            'url': button.url
        }

    def _quick_reply(self, reply: QuickReply):
        response = {
            "content_type": 'text',
            'title': reply.title[:20],
            'payload': json.dumps(reply.payload or {})
        }
        if reply.image_url:
            response['image_url'] = reply.image_url
        return response

    def _card_template(self, card: CardTemplate):
        response = {
            "title": card.title,
            "image_url": card.image_url,
            "subtitle": card.subtitle,
            "item_url": card.item_url
        }
        if card.buttons:
            response["buttons"] = [self.transform_message(button) for button in card.buttons]
        return response

    def _list_template(self, list: ListTemplate):
        response = {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "list",
                    'top_element_style': 'compact' if list.compact else 'large',
                    "elements": [self.transform_message(element) for element in list.elements[:4]]
                }
            }
        }
        if list.button:
            response['attachment']['payload']['buttons'] = [self.transform_message(list.button)]

        return response

    def _carousel_template(self, list: CarouselTemplate):
        return {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": [self.transform_message(element) for element in list.elements[:10]]
                }
            }
        }

    def _attachment_message(self, message: AttachmentMessage):
        return {
            "attachment": {
                "type": message.attachment_type,
                "payload": {
                    "url": message.url
                }
            }
        }

    def _media_message(self, message: MediaMessage):
        data = {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "media",
                    "elements": [
                        {
                            "media_type": message.media_type,
                        }
                    ]
                }
            }
        }

        if self._is_facebook_url(message.url):
            data['attachment']['payload']['elements'][0]['url'] = message.url
        else:
            att_id = self._retrieve_attachment(message.url)
            # yes it could expire in the 1e-5 seconds between prepare_message and this
            data['attachment']['payload']['elements'][0]['attachment_id'] = att_id

        data['attachment']['payload']['elements'][0]['buttons'] = [
            self.transform_message(button) for button in message.buttons
        ]

        return data
