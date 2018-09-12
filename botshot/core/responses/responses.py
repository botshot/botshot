from typing import Iterable
from botshot.core.serialize import json_serialize


class MenuElement:
    def __init__(self, type, title, payload=None, url=None,
                 webview_height_ratio=None, messenger_extensions=None):
        self.type = type
        self.title = title
        self.payload = payload
        self.url = url
        self.buttons = []

    def __str__(self):
        text = 'element: ' + self.title
        return text

    def add_button(self, button):
        self.buttons.append(button)
        return button


class MessageElement:
    """
    Base class for message elements.
    """

    def get_text(self):
        # FIXME: get text in more foolproof way
        return self.text if hasattr(self, 'text') else None

    def set_message_tag(self, tag):
        self.tag = tag

    def get_message_tag(self):
        """
        See https://developers.facebook.com/docs/messenger-platform/send-messages/message-tags
        :return: FB message tag
        """
        if hasattr(self, "tag"):
            return self.tag
        return None

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self)


class SenderActionMessage(MessageElement):
    def __init__(self, action):
        self.action = action

    def to_message(self, fbid):
        return {'sender_action': self.action, 'recipient': {"id": fbid}}


class TextMessage(MessageElement):
    """
    A plain text message. You can attach buttons or quick replies.
    """

    def __init__(self, text='', buttons=None, quick_replies=None):
        from .quick_reply import QuickReply
        self.text = text
        self.buttons = buttons if buttons else []
        self.quick_replies = [QuickReply(**reply) for reply in quick_replies or []]

    def __str__(self):
        text = self.text
        for button in self.buttons:
            text += "\n " + str(button)
        for reply in self.quick_replies:
            text += "\n " + str(reply)
        return text

    def add_button(self, button):
        if self.quick_replies:
            raise ValueError('Cannot add quick_replies and buttons to the same message')
        self.buttons.append(button)
        return self

    def add_reply(self, quick_reply):
        return self.add_quick_reply(quick_reply)

    def add_quick_reply(self, quick_reply):
        if self.buttons:
            raise ValueError('Cannot add quick_replies and buttons to the same message')
        elif isinstance(quick_reply, str):
            from botshot.core.responses.quick_reply import QuickReply
            quick_reply = QuickReply(title=quick_reply)

        self.quick_replies.append(quick_reply)
        return self

    def create_quick_reply(self, title=None, payload=None, image_url=None):
        from .quick_reply import QuickReply
        quick_reply = QuickReply(title=title, payload=payload, image_url=image_url)
        return self.add_quick_reply(quick_reply)

    def with_replies(self, replies: Iterable):
        if isinstance(replies, dict):
            for reply, state in replies.items():
                self.create_quick_reply(reply, payload={'_state': state})
        else:
            for reply in replies:
                self.add_quick_reply(reply)
        return self

    def with_buttons(self, buttons: Iterable):
        for button in buttons:
            self.add_button(button)
        return self


class AttachmentMessage(MessageElement):
    def __init__(self, attachment_type, url):
        self.attachment_type = attachment_type
        self.url = url


# TODO stickers not yet supported by Messenger :(
# class StickerMessage(MessageElement):
#    def __init__(self, sticker_id):
#        self.sticker_id = sticker_id
#
#    def to_response(self):
#        return {
#            "sticker_id": self.sticker_id
#        }


def _ellipsize(text, max_len=80):
    if text is None:
        return None
    if len(text) >= max_len:
        return text[:max_len-5] + "..."
    return text


def _get_payload_string(payload):
    text = ''
    for entity, values in payload.items():
        if isinstance(values, list):
            for value in values:
                text += '/{}/{}/ '.format(entity, value)
            break
        text += '/{}/{}/ '.format(entity, values)
    return text
