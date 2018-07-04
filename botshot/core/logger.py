import logging
import time

from django.conf import settings

from botshot.core.logging.abs_logger import MessageLogger


# ! DON'T IMPORT THIS FILE FROM settings.py !


class MessageLogging:

    def __init__(self, dialog):
        self.loggers = []
        self.dialog = dialog

    def log_user_message(self, type_, entities, accepted_time, accepted_state):
        """
        Log user message to all registered loggers.
        :param type_:           One of: message, postback, schedule
        :param entities:        A dict containing all the message entities
        :param accepted_time:   Unix timestamp - when was the message processed
        :param accepted_state:  Conversation state after processing the message
        :return:
        """
        # TODO this has to be called async

        # get raw message text for display
        message_text = entities.get("_message_text")
        if message_text and 'value' in message_text[0]:
            message_text = message_text[0]["value"]
        else:
            message_text = "({})".format(type_)

        for logger in MESSAGE_LOGGERS:
            logger.log_user_message(self.dialog, accepted_time, accepted_state, message_text, type_, entities)

    def log_bot_message(self, message, state):
        for logger in MESSAGE_LOGGERS:
            logger.log_bot_message(self.dialog, int(time.time()), state, message)

    def log_error(self, exception, state):
        for logger in MESSAGE_LOGGERS:
            logger.log_error(self.dialog, state, exception)

    def log_user(self, chat_session):
        for logger in MESSAGE_LOGGERS:
            logger.log_user(self.dialog, chat_session)


MESSAGE_LOGGERS = []


def register_logger(logger):
    if isinstance(logger, MessageLogger):
        logging.debug("Registering logger %s", logger.__class__.__name__)
        MESSAGE_LOGGERS.append(logger)
    else:
        raise ValueError("Error: Must be an instance of botshot.core.abs_logger.MessageLogger")


try:
    for item in settings.BOT_CONFIG.get("MESSAGE_LOGGERS", []):
        register_logger(item)
except Exception as ex:
    raise ValueError("Error registering message loggers, is your configuration correct?") from ex
