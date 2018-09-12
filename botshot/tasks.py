import logging
import time
import traceback

from celery import shared_task
from celery.task.schedules import crontab
from celery.utils.log import get_task_logger
from django.conf import settings

from botshot.core.chat_session import ChatSession
from botshot.core.interfaces import create_from_name
from botshot.core.persistence import get_redis
# Load logging service to be registered by celery
from botshot.core.logging import logging_service

logger = get_task_logger(__name__)


@shared_task
def accept_user_message(session: dict, raw_message):
    from botshot.core.dialog_manager import DialogManager
    session = ChatSession.from_json(session)
    print("Accepting message - chat id {}, message: {}".format(session.chat_id, raw_message))

    dialog = DialogManager(session)
    parsed = session.interface.parse_message(raw_message)
    _process_message(dialog, parsed)
    return True  # FIXME


def setup_schedule_callbacks(sender, callback):
    callbacks = settings.BOT_CONFIG.get('SCHEDULE_CALLBACKS')
    if not callbacks:
        return

    for name in callbacks:
        params = callbacks[name]
        print('Scheduling task {}: {}'.format(name, params))
        if isinstance(params, dict):
            cron = crontab(**params)
        elif isinstance(params, int):
            cron = params
        else:
            raise Exception(
                'Specify either number of seconds or dict of celery crontab params (hour, minute): {}'.format(params))
        sender.add_periodic_task(
            cron,
            callback.s(name),
        )
        print(' Scheduled for {}'.format(cron))


def accept_schedule_all_users(callback_name):
    print('Accepting scheduled callback {}'.format(callback_name))
    db = get_redis()
    interface_names = db.hgetall('session_interface')
    for uid in interface_names:
        interface_name = interface_names[uid].decode('utf-8')
        # TODO revise this
        interface = create_from_name(interface_name)
        session = ChatSession(interface, uid.decode('utf-8'))
        accept_schedule_callback(session.to_json(), callback_name)


@shared_task
def accept_schedule_callback(session: dict, callback_state):
    session = ChatSession.from_json(session)
    from botshot.core.dialog_manager import DialogManager
    db = get_redis()
    active_time = float(db.hget('session_active', session.chat_id).decode('utf-8'))
    inactive_seconds = time.time() - active_time
    print('{} from {} was active {}'.format(session.chat_id, session.interface, active_time))
    parsed = {
        'type': 'schedule',
        'entities': {
            '_inactive_seconds': inactive_seconds,
            '_state': callback_state
        }
    }
    dialog = DialogManager(session)
    _process_message(dialog, parsed)


@shared_task
def accept_inactivity_callback(session: dict, context_counter, callback_state, inactive_seconds):
    session = ChatSession.from_json(session)
    from botshot.core.dialog_manager import DialogManager
    dialog = DialogManager(session)

    # User has sent a message, cancel inactivity callback
    if dialog.context.counter != context_counter:
        print('Canceling inactivity callback after user message.')
        return

    parsed = {
        'type': 'schedule',
        'entities': {
            '_inactive_seconds': inactive_seconds,
            '_state': callback_state
        }
    }

    _process_message(dialog, parsed)


def _process_message(dialog, parsed):
    try:
        dialog.process(parsed['type'], parsed['entities'])
    except Exception as e:
        print("!!!!!!!!!!!!!!!! EXCEPTION AT MESSAGE QUEUE !!!!!!!!!!!!!!!", e)
        traceback.print_exc()
        dialog.logger.log_error(exception=e, state=dialog.current_state_name)


@shared_task
def fake_move_to_state(chat_id, state: str, entities=()):
    # TODO solve chat session saving and restoring
    session = get_redis().hget("chat_session", chat_id)

    if not (session and state):
        logging.warning("ChatSession or State is null")
        return

    import json
    session = json.loads(session.decode('utf-8'))
    session = ChatSession.from_json(session)
    state = str(state)
    from botshot.core.dialog_manager import DialogManager
    logger.debug("Moving chat id {} to state {}".format(session.chat_id, state))
    dialog = DialogManager(session)
    msg_data = {'_state': state}
    for k, v in entities:
        msg_data[k] = [{"value": v}]
    dialog.process('schedule', msg_data)
