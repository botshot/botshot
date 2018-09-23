from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
# Load logging service to be registered by celery
from botshot.core.logging import logging_service
from django.utils.timezone import is_naive

logger = get_task_logger(__name__)


def run_async(method, at=None, seconds=None, **kwargs):
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
        if is_naive(at):
            raise ValueError('Use datetime with timezone, e.g. "from django.utils import timezone"')
        celery_method_call_wrapper.apply_async(args=(method, ), eta=at, kwargs=kwargs)
    elif seconds is not None:
        celery_method_call_wrapper.apply_async(args=(method, ), countdown=seconds, kwargs=kwargs)
    else:
        celery_method_call_wrapper.delay(method, **kwargs)

@shared_task
def celery_method_call_wrapper(method, **kwargs):
    return method(**kwargs)

