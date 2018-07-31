import json
import logging
from typing import List, Optional

from botshot.core.responses import CarouselMessage
from botshot.core.responses.buttons import Button, LinkButton, PayloadButton
from botshot.core.responses.quick_reply import QuickReply, LocationQuickReply
from botshot.core.responses.responses import *
from botshot.core.responses.templates import ListTemplate


from botshot.core.interfaces.adapter.message_adapter import MessageAdapter
from botshot.core.responses import *


class TelegramAdapter(MessageAdapter):

    def __init__(self):
        super().__init__()

        self.functions = {
            TextMessage: self._text_message,

            # Buttons
            # LinkButton: self._link_button,
            # PayloadButton: self._payload_button,
            # PhoneButton: self._phone_button,
            # ShareButton: lambda button: {'type': 'element_share'},
            # AccountLinkButton: self._account_link_button,
            # AccountUnlinkButton: lambda button: {'type': 'account_unlink'},

            # Quick replies
            # QuickReply: self._quick_reply,
            # LocationQuickReply: lambda reply: {'content_type': 'location'},

            # Templates
            # CardMessage: self._card_template,
            # ListTemplate: self._list_template,
            # CarouselMessage: self._carousel_template,

            # Media
            AttachmentMessage: self._attachment_message,
            # MediaMessage: self._media_message,
        }

    def transform_message(self, message: MessageElement, session=None):
        message_type = type(message)
        fn = self.functions.get(message_type)
        if not fn:
            raise Exception("Response {} is not supported in Telegram at the moment!".format(message_type))
        return fn(message, session)

    def prepare_message(self, message: MessageElement, session):
        pass

    def _text_message(self, message: TextMessage, session, parse_mode=None, silent=False) -> List[tuple]:
        """
        Builds a text message for telegram.
        :param text: Text of the message.
        :param session: ChatSession
        :param parse_mode: None, html or markdown. Don't forget to escape reserved chars!
        :param silent: Whether to notify the user with a beep, used when sending more messages in row
        :param reply: Quick replies, buttons, or anything of the sort
        :return: telegram method, payload
        """
        payload = {
            'chat_id': session.meta['chat_id'],
            'text': message.text
        }
        if parse_mode:
            payload['parse_mode'] = parse_mode
        if silent:
            payload['disable_notification'] = True

        if message.quick_replies:
            payload['reply_markup'] = json.dumps(self._quick_replies(message.quick_replies))
        elif message.buttons:
            payload['reply_markup'] = json.dumps(self._buttons(message.buttons))

        return [('sendMessage', payload)]

    def _attachment_message(self, message: AttachmentMessage, session, caption=None):
        payload = {
            'chat_id': session.meta['chat_id'],
            'photo': message.url,
            'disable_notification': False
        }
        if caption and isinstance(caption, str):
            payload['caption'] = caption[:200]
        return [('sendPhoto', payload)]

    def _quick_replies(self, replies: List[QuickReply]) -> dict:
        row = []
        for reply in replies:
            if isinstance(reply, LocationQuickReply):
                logging.warning('Skipping location quick reply, not supported')
                continue  # TODO support telegram location, keyboard <> inline keyboard
            key_button = {
                'text': reply.title
            }
            row.append(key_button)
        keyboard = [row]
        return {
            'keyboard': keyboard,
            'resize_keyboard': True,
            'one_time_keyboard': True
        }

    def _buttons(self, buttons: List[Button] or Button) -> Optional[dict]:
        if isinstance(buttons, Button):
            buttons = [buttons]
        row = []
        for button in buttons:
            key = None
            if isinstance(button, LinkButton):
                key = {
                    'text': button.title,
                    'url': button.url
                }
            elif isinstance(button, PayloadButton):
                payload = json.dumps(button.payload)
                from botshot.core.interfaces.telegram import TelegramInterface
                callback_data = TelegramInterface.persist_callback(payload)
                key = {
                    'text': button.title,
                    'callback_data': callback_data
                }
            else:
                logging.warning('Button class {} is not supported'.format(type(button)))
            if key:
                row.append(key)
        if not len(row):
            return None
        keyboard = [row]
        return {
            'inline_keyboard': keyboard
        }


class TelegramAdapter2():
    """To be removed"""

    def __init__(self, chat_id):
        try:
            self.id = int(chat_id)
        except ValueError:
            raise Exception('Chat id must be integer')

    def to_response(self, element) -> list:
        if isinstance(element, MessageElement):

            if isinstance(element, TextMessage):

                reply = None
                if element.quick_replies:
                    reply = self.quick_replies(element.quick_replies)
                elif element.buttons:
                    reply = self.buttons(element.buttons)

                return [self.text_message(element.text, reply=reply)]

            elif isinstance(element, CarouselMessage) or isinstance(element, ListTemplate):
                responses = []
                for e in element.elements:
                    title, subtitle = escape_markdown(e.title), escape_markdown(e.subtitle)
                    text = '*{}*\n{}'.format(title, subtitle)
                    buttons = self.buttons(e.buttons) if e.buttons else None
                    response = self.text_message(text, parse_mode='Markdown', silent=True, reply=buttons)
                    responses.append(response)
                    if e.image_url:
                        responses.append(self.photo_message(e.image_url, caption=e.title))
                if hasattr(element, 'button') and element.button:  # FIXME send without dummy message
                    btn = self.buttons(element.button)
                    if btn:
                        response = self.text_message('.', reply=btn)
                        responses.append(response)
                return responses

        response = str(element)
        if response:
            response = response[:1000]
        return [self.text_message(response)]

    def text_message(self, text, parse_mode=None, silent=False, reply=None) -> tuple:
        """
        Builds a text message for telegram.
        :param text: Text of the message.
        :param parse_mode: None, html or markdown. Don't forget to escape reserved chars!
        :param silent: Whether to notify the user with a beep, used when sending more messages in row
        :param reply: Quick replies, buttons, or anything of the sort
        :return: telegram method, payload
        """
        payload = {
            'chat_id': self.id,
            'text': text
        }
        if parse_mode:
            payload['parse_mode'] = parse_mode
        if silent:
            payload['disable_notification'] = True
        if reply:
            payload['reply_markup'] = json.dumps(reply)
        return 'sendMessage', payload

    def quick_replies(self, replies: List[QuickReply]) -> dict:
        row = []
        for reply in replies:
            if isinstance(reply, LocationQuickReply):
                logging.warning('Skipping location quick reply, not supported')
                continue  # TODO support telegram location, keyboard <> inline keyboard
            key_button = {
                'text': reply.title
            }
            row.append(key_button)
        keyboard = [row]
        return {
            'keyboard': keyboard,
            'resize_keyboard': True,
            'one_time_keyboard': True
        }

    def buttons(self, buttons: List[Button] or Button) -> Optional[dict]:
        if isinstance(buttons, Button):
            buttons = [buttons]
        row = []
        for button in buttons:
            key = None
            if isinstance(button, LinkButton):
                key = {
                    'text': button.title,
                    'url': button.url
                }
            elif isinstance(button, PayloadButton):
                payload = json.dumps(button.payload)
                from botshot.core.interfaces.telegram import TelegramInterface
                callback_data = TelegramInterface.persist_callback(payload)
                key = {
                    'text': button.title,
                    'callback_data': callback_data
                }
            else:
                logging.warning('Button class {} is not supported'.format(button.__class__.__name__))
            if key:
                row.append(key)
        if not len(row):
            return None
        keyboard = [row]
        return {
            'inline_keyboard': keyboard
        }

    def photo_message(self, photo_url: str, caption=None, silent=True):
        payload = {
            'chat_id': self.id,
            'photo': photo_url,
            'disable_notification': silent
        }
        if caption and isinstance(caption, str):
            payload['caption'] = caption[:200]
        return 'sendPhoto', payload


def escape_markdown(s: Optional[str]) -> Optional[str]:
    if s:
        return s.replace('*', '\*').replace('_', '\_')
    return None
