import json

from botshot.core.responses.responses import MessageElement, _get_payload_string
from botshot.core.serialize import json_serialize


class QuickReply(MessageElement):
    """
    A button with text that gets sent as message when clicked.
    """

    def __init__(self, title=None, payload=None, image_url=None):
        self.title = title
        self.payload = payload
        self.image_url = image_url

    def to_response(self):
        response = {
            "content_type": 'text',
            'title': self.title[:20],
            'payload': json.dumps(self.payload if self.payload else {}, default=json_serialize)
        }
        if self.image_url:
            response['image_url'] = self.image_url
        return response

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

    def to_response(self):
        return {'content_type': 'location'}

    def __str__(self):
        return str(super) + " location"
