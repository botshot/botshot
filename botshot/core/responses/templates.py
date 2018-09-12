from typing import List

from botshot.core.responses.responses import MessageElement, _ellipsize


class CardTemplate(MessageElement):
    """
    A horizontal card view with title, subtitle, image and buttons.
    """

    def __init__(self, title, image_url=None, subtitle=None, item_url=None, buttons=None):
        self.title = _ellipsize(str(title)) if title else None
        self.subtitle = _ellipsize(str(subtitle)) if subtitle else None
        self.image_url = image_url
        self.item_url = item_url
        self.buttons = buttons if buttons else []

    def to_response(self):
        response = {
            "title": self.title,
            "image_url": self.image_url,
            "subtitle": self.subtitle,
            "item_url": self.item_url
        }
        if self.buttons:
            response["buttons"] = [button.to_response() for button in self.buttons]
        return response

    def __str__(self):
        text = 'element: ' + self.title
        if self.subtitle:
            text += " (" + self.subtitle + ")"
        for button in self.buttons:
            text += "\n  " + str(button)
        return text

    def add_button(self, button):
        self.buttons.append(button)
        return self


class ListTemplate(MessageElement):

    def __init__(self, is_compact=False, button=None):
        super().__init__()
        self.elements = []  # type: List[CardTemplate]
        self.compact = is_compact
        self.button = button

    def add_element(self, element: CardTemplate):
        self.elements.append(element)
        return self

    def create_element(self, **kwargs):
        element = CardTemplate(**kwargs)
        return self.add_element(element)


class CarouselTemplate(MessageElement):
    """
    A horizontal list of GenericTemplateElement items.
    """

    def __init__(self, elements=None):
        self.elements = [CardTemplate(**element) for element in elements or []]

    def to_response(self):
        return {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": [element.to_response() for element in self.elements[:10]]
                }
            }
        }

    def __str__(self):
        text = 'generic template:'
        for element in self.elements:
            text += "\n " + str(element)
        return text

    def add_element(self, element):
        self.elements.append(element)
        return self

    def create_element(self, **kwargs) -> CardTemplate:
        element = CardTemplate(**kwargs)
        self.add_element(element)
        return element


