import json
from abc import ABC, abstractmethod

from botshot.core.responses.responses import MessageElement
from botshot.core.serialize import json_serialize


class Button(MessageElement, ABC):
    """
    An abstract chat button. Don't use this class directly.
    """

    @abstractmethod
    def to_response(self):
        raise NotImplementedError('Abstract method')

    @abstractmethod
    def __str__(self):
        raise NotImplementedError('Abstract method')


class PayloadButton(Button):
    """
    A button that sends predefined data back to the bot when clicked.
    """

    def __init__(self, title, payload):
        super(Button, self).__init__()
        self.title = title
        self.payload = payload

    def to_response(self):
        return {
            'title': self.title,
            'type': 'postback',
            'payload': json.dumps(self.payload, default=json_serialize)
        }

    def __str__(self):
        return 'button: {}: {}'.format(self.title, self.payload)


class LinkButton(Button):
    """
    A button that opens a website when clicked.
    """

    def __init__(self, title, url, webview=False):
        super(Button, self).__init__()
        self.title = title
        self.url = url
        self.webview_height_ratio = 'compact' if webview else 'full'

    def to_response(self):
        return {
            'title': self.title,
            'type': 'web_url',
            'url': self.url,
            'webview_height_ratio': self.webview_height_ratio
        }

    def __str__(self):
        return 'button: {}: {}'.format(self.title, self.url)


class PhoneButton(Button):
    """
    A button that calls a number when clicked.
    Currently only Facebook Messenger is supported.
    """

    def __init__(self, title, phone_number):
        super(Button, self).__init__()
        self.title = title
        self.phone_number = phone_number

    def to_response(self):
        return {
            'title': self.title,
            'type': 'phone_number',
            'payload': self.phone_number
        }

    def __str__(self):
        return 'button: {}: {}'.format(self.title, self.phone_number)


class AccountLinkButton(Button):
    """
    A button that shows the FB messenger account linking dialog when clicked.
    """

    def __init__(self, url):
        super(Button, self).__init__()
        self.url = url

    def to_response(self):
        return {
            'type': 'account_link',
            'url': self.url
        }

    def __str__(self):
        return 'button: account_link: {}'.format(self.url)


class AccountUnlinkButton(Button):
    """
    A button that shows the FB messenger account unlinking dialog when clicked.
    """

    def __init__(self, url):
        super(Button, self).__init__()
        self.url = url

    def to_response(self):
        return {
            'type': 'account_unlink'
        }

    def __str__(self):
        return 'button: account_unlink'


class ShareButton(Button):
    """
    A button that opens share dialog for the message it's attached to.
    Currently only Facebook Messener is supported.
    Can be attached to list, carousel and media templates.
    """

    def __init__(self):
        super(Button, self).__init__()

    def to_response(self):
        return {
            'type': 'element_share'
        }

    def __str__(self):
        return 'button: share'
