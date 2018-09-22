class RawMessage:
    def __init__(self, interface, raw_user_id, user_meta, raw_chat_id, chat_meta, type, text, payload, timestamp):
        self.interface = interface
        self.raw_user_id = raw_user_id
        self.user_meta = user_meta
        self.raw_chat_id = raw_chat_id
        self.chat_meta = chat_meta
        self.type = type
        self.text = text
        self.payload = payload
        self.timestamp = timestamp