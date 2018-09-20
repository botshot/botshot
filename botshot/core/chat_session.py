
class ChatSession:
    def __init__(self, interface, unique_id, profile=None, is_test=False, meta=None):
        """
        :param interface: Chat interface object
        :param unique_id: Identifier of this chat
        """
        if interface is None:
            raise ValueError("Interface must be set")
        self.interface = interface
        self.chat_id = unique_id
        self.profile = profile or Profile()
        self.is_test = is_test
        self.meta = meta

    def accept(self, raw_message):
        from botshot.tasks import accept_user_message
        accept_user_message.delay(session=self, raw_message=raw_message)

    @staticmethod
    def create_chat_id(interface):
        unique_id = interface.get_unique_id()
        if unique_id is None:
            raise ValueError('Interface {} provided null unique id'.format(interface))
        return "{}_{}".format(interface.prefix, unique_id)


class Profile:
    def __init__(self, first_name=None, last_name=None, tmp_image_url=None, tmp_image_extension=None, locale=None):
        self.first_name = first_name
        self.last_name = last_name
        self.tmp_image_url = tmp_image_url
        self.tmp_image_extension = tmp_image_extension
        self.locale = locale

    def __str__(self):
        return 'Profile({})'.format(str(self.__dict__))
