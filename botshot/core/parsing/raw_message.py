
class RawMessage:
    def __init__(self, interface, raw_user_id, raw_conversation_id, conversation_meta, type, text, payload, timestamp):
        from botshot.core.interfaces import BotshotInterface
        self.interface: BotshotInterface = interface
        self.raw_user_id = raw_user_id
        self.raw_conversation_id = raw_conversation_id
        self.conversation_meta = conversation_meta
        self.type = type
        self.text = text
        self.payload = payload
        if timestamp < 1e10:
            raise ValueError("Timestamp value should be in milliseconds, got: {}.".format(timestamp))
        self.timestamp = timestamp