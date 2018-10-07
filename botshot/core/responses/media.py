from botshot.core.responses import MessageElement


class MediaMessage(MessageElement):
    def __init__(self, url, buttons=None, media_type="image", allow_cache=True):
        self.url = url
        self.media_type = media_type
        self.allow_cache = allow_cache
        self.buttons = buttons or []

    def to_response(self):
        return {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "media",
                    "elements": [
                        {
                            "media_type": self.media_type,
                            "attachment_id": "<ATTACHMENT_ID>"
                        }
                    ]
                }
            }
        }
