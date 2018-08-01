import logging
from typing import Optional

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
            CardTemplate: self._card_template,
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

    def _card_template(self, message: CardTemplate, session):

        # FIXME html encode title, subtitle
        item_url = "<a>{url}</a>".format(url=message.item_url) if message.item_url else ""
        html_text = "<strong>{title}</strong>\n{subtitle}\n{url}".format(
            title=message.title, subtitle=message.subtitle, url=item_url
        )

        payload = {
            'chat_id': session.meta['chat_id'],
            'parse_mode': "HTML",
            'text': html_text,
            'disable_web_page_preview': False
        }

        # if message.quick_replies:  TODO should they be added to the template?
        #     payload['reply_markup'] = json.dumps(self._quick_replies(message.quick_replies))
        if message.buttons:
            payload['reply_markup'] = json.dumps(self._buttons(message.buttons))

        photo_payload = {  # TODO image aspect ratio would be nice
            'chat_id': session.meta['chat_id'],
            'photo': message.image_url,
            'disable_notification': True,
            'caption': message.title[:200] if message.title else None,
        }
        return [('sendPhoto', photo_payload), ('sendMessage', payload)]


def escape_markdown(s: Optional[str]) -> Optional[str]:
    if s:
        return s.replace('*', '\*').replace('_', '\_')
    return None
