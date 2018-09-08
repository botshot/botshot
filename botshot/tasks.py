import logging
import time
import traceback

from celery import shared_task
from celery.task.schedules import crontab
from celery.utils.log import get_task_logger
from django.conf import settings

from botshot.core.chat_session import ChatSession
from botshot.core.interfaces.all import create_from_name
from botshot.core.parsing.user_message import UserMessage
# Load logging service to be registered by celery
from botshot.core.logging import logging_service

logger = get_task_logger(__name__)


@shared_task
def accept_user_message(session, raw_message):
    from botshot.core.dialog_manager import DialogManager
    print("Accepting message - chat id {}, message: {}".format(session.chat_id, raw_message))

    dialog = DialogManager(session)
    message: UserMessage = session.interface.parse_message(raw_message)
    _process_message(dialog, session, message)


# TODO: Make scheduled callbacks work again
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
    from botshot.core.dialog_manager import DialogManager
    print('Accepting scheduled callback {}'.format(callback_name))
    chat_ids_to_interface_names = DialogManager.get_interface_chat_ids()
    for chat_id in chat_ids_to_interface_names:
        interface_name = chat_ids_to_interface_names[chat_id].decode('utf-8')
        # TODO revise this
        interface = create_from_name(interface_name)
        session = ChatSession(interface, chat_id.decode('utf-8'))
        accept_schedule_callback(session, callback_name)


@shared_task
def accept_schedule_callback(session: ChatSession, callback_state):
    from botshot.core.dialog_manager import DialogManager
    dialog = DialogManager(session)
    active_time = dialog.get_active_time()
    inactive_seconds = time.time() - active_time
    print('{} from {} was active {}'.format(session.chat_id, session.interface, active_time))
    message = UserMessage('schedule', payload={
            '_inactive_seconds': inactive_seconds,
            '_state': callback_state
    })
    _process_message(dialog, session, message)


@shared_task
def accept_inactivity_callback(session: ChatSession, context_counter, callback_state, inactive_seconds):
    from botshot.core.dialog_manager import DialogManager
    dialog = DialogManager(session)

    # User has sent a message, cancel inactivity callback
    if dialog.context.counter != context_counter:
        print('Canceling inactivity callback after user message.')
        return

    message = UserMessage('schedule', payload={
        '_inactive_seconds': inactive_seconds,
        '_state': callback_state
    })

    _process_message(dialog, session, message)


def _process_message(dialog, session: ChatSession, message: UserMessage):
    try:
        dialog.process(message)
    except Exception as e:
        print("!!!!!!!!!!!!!!!! EXCEPTION AT MESSAGE QUEUE !!!!!!!!!!!!!!!", e)
        traceback.print_exc()
        from botshot.core.logging import logging_service
        logging_service.log_error(session=session, exception=e, state=dialog.current_state_name)
