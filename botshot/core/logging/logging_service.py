import logging
import time
import importlib
from typing import List
from celery import shared_task

from django.conf import settings

from botshot.core.logging.abs_logger import MessageLogger
from botshot.core.chat_session import ChatSession
import traceback

MESSAGE_LOGGERS: List[MessageLogger] = []


def init():
    global MESSAGE_LOGGERS
    MESSAGE_LOGGERS = []

    if 'MESSAGE_LOGGERS' not in settings.BOT_CONFIG:
        # FIXME: Config should be validated in one place
        raise ValueError("Missing required field 'MESSAGE_LOGGERS' in BOT_CONFIG.")

    for module_class_path in settings.BOT_CONFIG['MESSAGE_LOGGERS']:
        if '.' not in module_class_path:
            raise ValueError('Use fully qualified name in BOT_CONFIG.MESSAGE_LOGGERS (module.path.LoggerClass)')
        package, classname = module_class_path.rsplit('.', maxsplit=1)
        module = importlib.import_module(package)
        klass = getattr(module, classname)
        logger: MessageLogger = klass()
        MESSAGE_LOGGERS.append(logger)


@shared_task
def log_user_message(session: ChatSession, state, message, entities):
    """
    Log user message to all registered loggers.
    :param session:         Current ChatSession
    :param state:           Conversation state after processing the message
    :param message:         Given UserMessage
    :param entities:        A dict containing all the message entities
    :return:
    """

    log_all_safe(lambda logger: logger.log_user_message(session, state, message, entities))


@shared_task
def log_bot_message(session: ChatSession, sent_time, state, response):
    log_all_safe(lambda logger: logger.log_bot_message(session, sent_time, state, response))


@shared_task
def log_error(session: ChatSession, state, exception):
    log_all_safe(lambda logger: logger.log_error(session, state, exception))


def log_all_safe(func):
    for logger in MESSAGE_LOGGERS:
        try:
            func(logger)
        except Exception as e:
            print('Error logging to "{}": {}'.format(logger, e))
            traceback.print_exc()


def _import_full_name(classname):
    package, classname = classname.rsplit('.', maxsplit=1)
    module = importlib.import_module(package)
    return getattr(module, classname)
