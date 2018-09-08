import logging


_interfaces = []


def add_interface(classname):
    """
    Adds a messaging interface for a messaging platform.
    :param classname:
    :return:
    """
    import importlib

    package, classname = classname.rsplit(".", maxsplit=1)
    module = importlib.import_module(package)
    cls = getattr(module, classname)

    _interfaces.append(cls)


def get_interfaces():
    """
    :returns: List of all registered chat interface classes.
    """
    from botshot.core.interfaces.facebook import FacebookInterface
    from botshot.core.interfaces.telegram import TelegramInterface
    from botshot.core.interfaces.microsoft import MicrosoftInterface
    from botshot.core.interfaces.google import GoogleActionsInterface
    from botshot.core.interfaces.test import TestInterface
    from botshot.webchat.interface import WebchatInterface
    return [FacebookInterface, TelegramInterface, MicrosoftInterface, GoogleActionsInterface,
                         TestInterface, WebchatInterface] + _interfaces


def create_from_name(name):
    ifs = get_interfaces()
    for interface in ifs:
        if interface.name == name:
            return interface
    raise ValueError('Interface with name "{}" not registered'.format(name))


def create_from_prefix(prefix):
    ifs = get_interfaces()
    for interface in ifs:
        if interface.prefix == prefix:
            return interface
    raise ValueError('Interface with prefix "{}" not registered'.format(prefix))


def init_webhooks():
    """
    Registers webhooks for telegram messages.
    """
    logging.debug('Trying to register telegram webhook')
    try:
        from botshot.core.interfaces.telegram import TelegramInterface
        TelegramInterface.init_webhooks()
    except Exception as e:
        logging.exception('Couldn\'t init webhooks')


def uid_to_interface_name(uid: str):
    prefix = str(uid).split('_')[0]

    for i in get_interfaces():
        if i.prefix == prefix:
            return i.name
    raise Exception('No interface for {}'.format(uid))
