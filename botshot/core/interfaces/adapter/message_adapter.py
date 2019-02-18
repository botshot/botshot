from abc import ABC, abstractmethod

from botshot.core.responses import MessageElement


class MessageAdapter(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def transform_message(self, message: MessageElement, conversation_meta):
        """
        Transform a message to messaging platform's native format.
        :param message: Instance of MessageElement.
        :param conversation_meta: Dict with ChatConversation metadata.
        :returns: the transformed message object
        """
        pass
