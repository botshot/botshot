import logging
from datetime import datetime, timedelta
from django.utils import timezone
import pytz

from celery import shared_task
from celery.signals import beat_init, celeryd_init

from botshot.models import ScheduledAction, ChatUser, ChatConversation
from botshot.core.responses import MessageElement
from botshot.core.chat_manager import ChatManager
from botshot.core.parsing.raw_message import RawMessage
from botshot.core.conversation_filter import ConversationFilter, ListConversationFilter

from django.db.models.signals import post_save, post_delete


TASK_TIMEOUT = timedelta(hours=1)


class MessageScheduler:

    def add_schedule(self, action, conversations, at: datetime, description=None) -> str:
        """
        Schedules an action.

        :param action:          either a dict containing payload or a MessageElement
        :param conversations:   conversations for which the schedule will be executed
                                You can provide a ConversationFilter object, a list or one id.
        :param at:              localized datetime, when to send the schedule
        :param description:     (optional) short human-readable description of event
        :return: ID of this schedule
        """

        conversations = self._validate_conversation_filter(conversations)
        self._validate_action(action)
        at = self._validate_datetime(at)
        schedule = ScheduledAction(_at=at, action=action, 
            description=description, 
            conversations=conversations)
        schedule.save()
        task_id = "botshot_schedule_{}".format(schedule.pk)
        return task_id
    
    def add_recurrent_schedule(
        self, action, conversations, 
        hour=None, minute=None, second=None, 
        weekday=None, day=None, month=None, 
        until=None, description=None
    ) -> str:
        """
        Schedules a recurrent action.
        The time specification must be in UTC.

        :param action:          either a dict containing payload or a MessageElement
        :param conversations:   conversations for which the schedule will be executed
                                You can provide a ConversationFilter object, a list or one id.
        :param until:           localized datetime, when to remove the schedule
        :param description:     (optional) short human-readable description of event
        :return: ID of this schedule
        """

        timespec = {
            "hour": hour,
            "minute": minute,
            "second": second,
            "day_of_week": weekday,
            "day_of_month": day,
            "month_of_year": month
        }
        conversations = self._validate_conversation_filter(conversations)
        self._validate_timespec(timespec)
        self._validate_action(action)
        at = MessageScheduler._nearest_datetime(timespec)  # tz-naive
        at = at.replace(tzinfo=pytz.UTC)
        print("WILL RUN @ {}".format(at))
        until = self._validate_datetime(until) if until else None
        schedule = ScheduledAction(recurrence=timespec, _at=at, _until=until, 
            action=action, description=description, 
            conversations=conversations)
        schedule.save()
        task_id = "botshot_schedule_{}".format(schedule.pk)
        return task_id

    def remove_schedule(self, schedule_id):
        if not schedule_id or not schedule_id.startswith("botshot_schedule_"):
            raise Exception("Invalid schedule ID")
        db_key = schedule_id[len("botshot_schedule_"):]
        schedule = ScheduledAction.objects.get(pk=db_key)
        schedule.delete()

    def list_schedules(self):
        return ScheduledAction.objects.all()

    @staticmethod
    @shared_task(name='botshot.schedule_wrapper', bind=True)
    def _schedule_wrapper(self, conversations: ConversationFilter, action, task_id=None):
        logging.debug("Running schedule %s", task_id)
        conversations = conversations.get_ids()

        if isinstance(action, dict):
            # Botshot state + context schedule, different for each conversation
            manager = ChatManager()
            for id in conversations:
                manager.accept_scheduled(
                    conversation_id=id, user_id=None, payload=action)
        elif isinstance(action, MessageElement):
            # Prepared MessageElement schedule, sent as a broadcast
            for id in conversations:  # TODO: this has to be done in one query
                conversation = ChatConversation.objects.get(conversation_id=id)
                try:
                    conversation.interface.send_responses(conversation, None, action)
                except Exception:
                    logging.exception("Can't send scheduled message to chat")
        else:
            logging.error("Unknown schedule action type: {}".format(type(action)))
            raise NotImplementedError()

    @staticmethod
    @shared_task
    def heartbeat():
        now = timezone.now()
        actions_to_run = []
        # delete expired schedules
        ScheduledAction.objects.filter(_until__lt=now).delete()
        # select tasks to run
        for schedule in ScheduledAction.objects.filter(_at__lte=now, is_done=False):
            if schedule.at >= now - TASK_TIMEOUT:
                # task is recent enough to run
                actions_to_run.append((schedule._id, schedule.conversations, schedule.action))
            # either way, if the task is periodic, set it to run next time
            # TODO: test how this behaves with very short time intervals
            if schedule.recurrence:
                # update _at to first matching future time
                nearest = MessageScheduler._nearest_datetime(schedule.recurrence)  # tz-naive
                schedule._at = nearest.replace(tzinfo=pytz.UTC)
                schedule.save()           # saved for future run
            else:
                # one-time schedule, we can't risk running it twice
                if schedule.description:  # human-triggered
                    schedule.is_done = True  # TODO: is_active would be better
                    schedule.save()       # saved for future reference
                else:                     # automatic (no description)
                    schedule.delete()     # not needed, deleted
        # run selected tasks
        for task_id, conversations, action in actions_to_run:
            MessageScheduler._schedule_wrapper.delay(conversations, action, task_id)

    @staticmethod
    def _nearest_datetime(timespec: dict):  # timespec has to be in UTC!
        # TODO: test me!
        now = datetime.now()

        month = timespec.get('month_of_year')
        date = timespec.get('day_of_month')
        weekday = timespec.get('day_of_week')

        hour = timespec.get('hour')
        minute = timespec.get('minute')
        second = timespec.get('second') or 0

        if minute is None:
            dt = now.replace(second=second)
            if dt <= now:
                dt += timedelta(minutes=1)
            return dt
        if hour is None:
            dt = now.replace(minute=minute, second=second)
            if dt <= now:
                dt += timedelta(hours=1)
            return dt
        if weekday is None and date is None:
            dt = now.replace(hour=hour, minute=minute, second=second)
            if dt <= now:
                dt += timedelta(days=1)
            return dt
        if date is None:  # weekday
            day_delta = weekday - now.weekday
            dt = now.replace(hour=hour, minute=minute, second=second) + timedelta(days=day_delta)
            if dt <= now:
                dt += timedelta(days=7)
            return dt
        if month is None: # date
            dt = datetime(year=now.year, month=now.month, day=date, hour=hour, minute=minute, second=second)
            if dt <= now:
                month, year = now.month + 1, now.year if now.month < 12 else 1, now.year + 1
                dt = datetime(year=year, month=month, day=date, hour=hour, minute=minute, second=second)
            return dt
        dt = datetime(year=now.year, month=month, day=date, hour=hour, minute=minute, second=second)
        if dt <= now:
            dt.replace(year=now.year+1)
        return dt

    def _validate_timespec(self, timespec: dict):
        try:
            if timespec.get('day_of_month') is not None and timespec.get('day_of_week') is not None:
                raise Exception("Timespec must contain at most one of: day_of_month, day_of_week")
            
            keys = ['minute', 'hour', 'day_of_month', 'month_of_year']
            ranges = {
                "second": (0, 59),
                "minute": (0, 59),
                "hour":   (0, 23),
                "day_of_month":  (1, 31),
                "day_of_week":   (0, 6),
                "month_of_year": (1, 12)
            }

            was_present = True
            last_key = "second"
            key_cnt = 1 if timespec.get('second') is not None else 0

            for key in keys:
                # every time interval requires the previous one to be present
                # for example, to repeat a task every hour we also need to know the minute
                is_present = timespec.get(key) is not None
                if key == 'day_of_month':
                    is_present |= timespec.get('day_of_week') is not None
                if is_present and not was_present:
                    raise Exception("When using %s in timespec, %s also needs to be present" % (key, last_key))
                
                was_present = is_present
                last_key = key
                if is_present: key_cnt += 1
            
            for key, range in ranges.items():
                value = timespec.get(key)
                if value is not None:
                    if value < range[0] or value > range[1]:
                        raise Exception("%s must be in range (%d, %d)" % (key, range[0], range[1]))

            if key_cnt <= 0:
                raise Exception("Timespec must contain at least one time key")

        except Exception as e:
            raise Exception("Invalid schedule specification") from e

    def _validate_conversation_filter(self, filter: any):
        if isinstance(filter, ConversationFilter):
            return filter
        elif isinstance(filter, int):
            return ListConversationFilter([filter])
        elif isinstance(filter, (list, tuple)):
            l = []
            for obj in filter:
                if isinstance(obj, ChatConversation):
                    l.append(obj.id)
                elif isinstance(obj, int):
                    l.append(obj)
                else:
                    raise ValueError("Invalid conversation filter, list entry must be int or ChatConversation")
            return ListConversationFilter(l)
        else:
            raise ValueError('Invalid conversation filter, pass instance of ConversationFilter, or (list of) ChatConversation(s) or IDs')

    def _validate_action(self, action):
        if not isinstance(action, dict) and not isinstance(action, MessageElement):
            raise Exception("Action parameter should be: "
                            "a) a dict with schedule payload, or "
                            "b) a MessageElement.")

    def _validate_datetime(self, dt):
        if dt is None or not isinstance(dt, datetime):
            raise Exception("Parameter must be instance of datetime.datetime")
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            raise Exception("Datetime must be tz-aware")
        return dt.astimezone(pytz.utc)  # this makes sure the database doesn't screw up


from celery import current_app
current_app.add_periodic_task(5.0, MessageScheduler.heartbeat.s())
