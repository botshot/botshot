import logging

from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils.timezone import is_naive

logger = get_task_logger(__name__)


def run_async(method, _at=None, _seconds=None, **kwargs):
    """
    Run function or method asynchronously using Celery. Function (or method and its class) needs to be serializable.
    :param method: Top-level function or class instance method. Needs to be serializable.
    :param _at: Schedule at given time (datetime with timezone)
    :param _seconds: Schedule after given number of _seconds
    :param args: Positional arguments to pass to function.
    :param kwargs: Keyword arguments to pass to function.
    :return:
    """
    if _at is not None:
        if is_naive(_at):
            raise ValueError('Use datetime with timezone, e.g. "from django.utils import timezone"')
        return celery_method_call_wrapper.apply_async(args=(method, ), eta=_at, kwargs=kwargs)
    elif _seconds is not None:
        return celery_method_call_wrapper.apply_async(args=(method, ), countdown=_seconds, kwargs=kwargs)
    else:
        return celery_method_call_wrapper.delay(method, **kwargs)


@shared_task
def celery_method_call_wrapper(method, **kwargs):
    task_id = celery_method_call_wrapper.request.id
    logging.info("Accepting task {} for method {}".format(task_id, method))
    already_done = get_set_task_flag(task_id)
    if not already_done:
        return method(**kwargs)
    else:
        logging.info("Prevented duplicate task {}!".format(task_id))


def get_set_task_flag(task_id):
    """Prevents duplicate scheduled tasks."""
    from botshot.core.persistence import get_redis
    redis = get_redis()
    key = "botshot_task_flag_{}".format(task_id)
    is_done = redis.exists(key)
    # remove the flag 3600 sec. after executing for the first time
    redis.set(name=key, value=1, ex=3600)
    return is_done
