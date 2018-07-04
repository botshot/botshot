from botshot.core.responses.responses import MenuElement


class ThreadSetting():
    def to_response(self):
        pass


class GreetingSetting(ThreadSetting):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return 'greeting_setting'


class GetStartedSetting(ThreadSetting):
    def __init__(self, payload):
        self.payload = payload

    def __str__(self):
        return 'get_started_setting'


class MenuSetting(ThreadSetting):
    def __init__(self, elements=None):
        self.elements = [MenuElement(**element) for element in elements or []]

    def __str__(self):
        text = 'menu:'
        for element in self.elements:
            text += "\n " + str(element)
        return text

    def add_element(self, element):
        self.elements.append(element)
        return element

    def create_element(self, **kwargs):
        element = MenuElement(**kwargs)
        return self.add_element(element)
