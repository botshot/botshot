from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
# Load logging service to be registered by celery
from botshot.core.logging import logging_service

logger = get_task_logger(__name__)


def run_async(method, at=None, seconds=None, *args, **kwargs):
    """
    Run function or method asynchronously using Celery. Function (or method and its class) needs to be serializable.
    :param method: Top-level function or class instance method. Needs to be serializable.
    :param at: Schedule at given time (datetime with timezone)
    :param seconds: Schedule after given number of seconds
    :param args: Positional arguments to pass to function.
    :param kwargs: Keyword arguments to pass to function.
    :return:
    """
    if at is not None:
        if at.tzinfo is None or at.tzinfo.utcoffset(at) is None:
            raise Exception('Use datetime with timezone, e.g. "from django.utils import timezone"')
        celery_method_call_wrapper.apply_async(method, eta=at, *args, **kwargs)
    elif seconds is not None:
        celery_method_call_wrapper.apply_async(method, countdown=seconds, *args, **kwargs)
    else:
        celery_method_call_wrapper.delay(method, *args, **kwargs)

@shared_task
def celery_method_call_wrapper(method, *args, **kwargs):
    return method(*args, **kwargs)

