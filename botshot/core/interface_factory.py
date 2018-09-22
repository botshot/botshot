from botshot.core.interfaces.messenger import MessengerInterface
from botshot.core.interfaces.telegram import TelegramInterface
from botshot.core.interfaces.microsoft import MicrosoftInterface
from botshot.core.interfaces.google import GoogleActionsInterface
from botshot.core.interfaces.test import TestInterface

INTERFACES = {
    "messenger": MessengerInterface,
    "telegram": TelegramInterface,
    "microsoft": MicrosoftInterface,
    "google": GoogleActionsInterface,
    "test": TestInterface
}

class InterfaceFactory:

    @staticmethod
    def from_name(name) -> :
        if name not in INTERFACES:
            raise ValueError("Unknown interface name '{}'".format(name))
        return INTERFACES.get(name)()