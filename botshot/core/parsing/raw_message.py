
class RawMessage:
    def __init__(self, interface, raw_user_id, raw_conversation_id, conversation_meta, type, text, payload, timestamp: float):
        """
        Creates a raw message.
        :param interface:               An instance of a subclass of botshot.core.interfaces.BotshotInterface.
        :param raw_user_id:             A user ID unique for the interface.
        :param raw_conversation_id:     A conversation ID unique for the interface.
        :param conversation_meta:       A dict containing any other information the interface needs about the message.
        :param type:                    TODO
        :param text:                    The text of the message.
        :param payload:                 Special data, such as postback from a clicked button.
        :param timestamp:               Time when the message was received in epoch seconds.
        """
        from botshot.core.interfaces import BotshotInterface
        self.interface = interface  # type: BotshotInterface
        self.raw_user_id = raw_user_id
        self.raw_conversation_id = raw_conversation_id
        self.conversation_meta = conversation_meta
        self.type = type
        self.text = text
        self.payload = payload
        if timestamp > 1e10:
            raise ValueError("Timestamp value should be in seconds, got: {}.".format(timestamp))
        self.timestamp = timestamp

    def __repr__(self):
        return 'RawMessage({})'.format(self.__dict__)
