import importlib
import logging
from typing import List

from celery import shared_task
from django.conf import settings

from botshot.core.logging.abs_logger import MessageLogger

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
def log_user_message(chat_id, accepted_time: float, state, message_type, entities):
    """
    Log user message to all registered loggers.
    :param chat_id:         Unique identifier of chat session (ChatSession.chat_id)
    :param message_type:    One of: message, postback, schedule
    :param entities:        A dict containing all the message entities
    :param accepted_time:   Unix timestamp - when was the message processed
    :param state:           Conversation state after processing the message
    :return:
    """

    message_texts = entities.get('_message_text', [])
    message_text = message_texts[0].get('value') if message_texts else None
    log_all_safe(lambda logger: logger.log_user_message(chat_id, accepted_time, state, message_text, message_type, entities))


@shared_task
def log_bot_message(chat_id, sent_time, state, message_text, message_type, message_dict):
    log_all_safe(lambda logger: logger.log_bot_message(chat_id, sent_time, state, message_text, message_type, message_dict))


@shared_task
def log_error(chat_id, state, exception):
    log_all_safe(lambda logger: logger.log_error(chat_id, state, exception))


@shared_task
def log_user(chat_id, session_dict):
    log_all_safe(lambda logger: logger.log_user(chat_id, session_dict))


def log_all_safe(func):
    for logger in MESSAGE_LOGGERS:
        try:
            func(logger)
        except Exception as e:
            logging.exception('Error logging to "{}"'.format(logger))


def _import_full_name(classname):
    package, classname = classname.rsplit('.', maxsplit=1)
    module = importlib.import_module(package)
    return getattr(module, classname)
