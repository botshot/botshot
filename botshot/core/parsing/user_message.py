import time

class UserMessage:
    def __init__(self, message_type: str, text: str=None, payload: dict=None, accepted_time:float=None):
        self.message_type: str = message_type
        self.accepted_time: float = accepted_time or time.time()
        self.text: str = text
        self.payload = payload or {}
