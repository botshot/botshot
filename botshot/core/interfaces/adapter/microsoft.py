from botshot.core.responses.buttons import *
from botshot.core.responses.responses import *
from botshot.core.responses.templates import *


class MicrosoftAdapter():
    def __init__(self, chat_id):
        self.chat_id = chat_id

    def to_response(self, element) -> dict:
        if isinstance(element, MessageElement):
            if isinstance(element, TextMessage):
                response = {"text": element.text}

                if element.quick_replies:
                    response["suggestedActions"] = {"actions": self.quick_replies(element.quick_replies)}
                elif element.buttons:
                    response["suggestedActions"] = {"actions": self.buttons(element.buttons)}

                return response
            elif isinstance(element, GenericTemplateMessage) or isinstance(element, ListTemplate):
                return self.generic_template(element)
                # TODO cards and lists

        return {"text": str(element)}

    def quick_replies(self, replies):
        return [{
            "type": "imBack",
            "title": q.title,
            "value": q.title
        } for q in replies]

    def buttons(self, buttons):
        arr = []
        for btn in buttons:
            if isinstance(btn, LinkButton):
                arr.append({
                    "type": "openUrl",
                    "title": btn.title,
                    "value": btn.url
                })
            elif isinstance(btn, PayloadButton):
                arr.append({
                    "type": "postBack",
                    "title": btn.title,
                    "value": btn.payload
                })
            elif isinstance(btn, PhoneButton):
                arr.append({
                    "type": "call",
                    "title": btn.title,
                    "value": btn.phone_number
                })
                # TODO other buttons
        return arr

    def generic_template(self, template: GenericTemplateMessage or ListTemplate):
        if isinstance(template, GenericTemplateMessage):
            content_type = "application/vnd.microsoft.card.hero"
        elif isinstance(template, ListTemplate):
            content_type = "application/vnd.microsoft.card.thumbnail"
        else:
            raise Exception('Invalid template parameter')
        response = {
            "attachments": [
                {
                    "contentType": content_type,
                    "content": {
                        "title": elem.title,
                        # "subtitle": elem.subtitle,
                        "text": elem.subtitle[:1000],
                        "images": [{
                            "url": elem.image_url,
                            "alt": "event picture",
                            "tap": {
                                "type": "openUrl",
                                "value": elem.item_url
                            }
                        }],
                        "buttons": self.buttons(elem.buttons)
                    }
                }
                for elem in template.elements
            ]
        }
        return response
