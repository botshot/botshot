from abc import ABC, abstractmethod

from botshot.core.responses import MessageElement


class MessageAdapter(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def transform_message(self, message: MessageElement, session):
        """
        Transform a message to messaging platform's native format.
        :param message: Instance of MessageElement.
        :param session: Instance of ChatSession.
        :returns: the transformed message object
        """
        pass

    @abstractmethod
    def prepare_message(self, message: MessageElement, session):
        """
        Do any additional work you have to do in this method,
        such as caching or uploading images.
        Called before transform_message.
        :param message: Instance of MessageElement.
        :param session: Instance of ChatSession.
        :returns: Nothing.
        """
        pass
