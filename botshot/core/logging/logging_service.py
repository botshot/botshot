import logging
from typing import List

from celery import shared_task
from django.conf import settings

from botshot.core.logging.abs_logger import MessageLogger
from django.utils.module_loading import import_string

MESSAGE_LOGGERS: List[MessageLogger] = []


def init():
    global MESSAGE_LOGGERS
    MESSAGE_LOGGERS = []

    if 'MESSAGE_LOGGERS' not in settings.BOT_CONFIG:
        raise ValueError("Missing required field 'MESSAGE_LOGGERS' in BOT_CONFIG.")

    for module_class_path in settings.BOT_CONFIG['MESSAGE_LOGGERS']:
        logger_class = import_string(module_class_path)
        logger: MessageLogger = logger_class()
        MESSAGE_LOGGERS.append(logger)


@shared_task
def log_user_message(session, state, message, entities):
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
def log_bot_message(session, sent_time, state, response):
    log_all_safe(lambda logger: logger.log_bot_message(session, sent_time, state, response))


@shared_task
def log_error(session, state, exception):
    log_all_safe(lambda logger: logger.log_error(session, state, exception))


def log_all_safe(func):
    for logger in MESSAGE_LOGGERS:
        try:
            func(logger)
        except Exception as e:
            logging.exception('Error logging to "{}"'.format(logger))
