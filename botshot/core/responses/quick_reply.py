import json

from botshot.core.responses.responses import MessageElement, _get_payload_string


class QuickReply(MessageElement):
    """
    A button with text that gets sent as message when clicked.
    """

    def __init__(self, title=None, payload=None, image_url=None):
        self.title = title
        self.payload = payload
        self.image_url = image_url

    def __str__(self):
        text = 'quick_reply: '
        if self.title:
            text += self.title + ': '
        if self.payload:
            text += _get_payload_string(self.payload)
        return text


class LocationQuickReply(QuickReply):
    """
    A button that asks for user's location when clicked.
    Currently only supported on Facebook Messenger.
    """

    def __init__(self):
        super().__init__()

    def __str__(self):
        return str(super) + " location"
