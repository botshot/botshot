from typing import List

from botshot.core.responses.responses import MessageElement, GenericTemplateElement


class ListTemplate(MessageElement):

    def __init__(self, is_compact=False, button=None):
        super().__init__()
        self.elements = []  # type: List[GenericTemplateElement]
        self.compact = is_compact
        self.button = button

    def add_element(self, element: GenericTemplateElement):
        self.elements.append(element)
        return self

    def create_element(self, **kwargs):
        element = GenericTemplateElement(**kwargs)
        return self.add_element(element)

    def to_response(self):
        response = {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "list",
                    'top_element_style': 'compact' if self.compact else 'large',
                    "elements": [element.to_response() for element in self.elements[:4]]
                }
            }
        }
        if self.button:
            response['attachment']['payload']['buttons'] = [self.button.to_response()]

        return response
