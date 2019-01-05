import logging
from datetime import datetime
from django.utils import timezone
import pytz

from celery.schedules import crontab
from celery import shared_task
from celery.signals import beat_init

from botshot.models import ScheduledAction
from botshot.core.responses import MessageElement


class MessageScheduler:

    def add_schedule(self, action, user: str, at: datetime, description=None) -> str:
        """
        Schedules an action for the future.

        :param action:          either a dict containing payload or a MessageElement
        :param user:            conversation_id where to send the schedule
        :param at:              localized datetime, when to send the schedule
        :param description:     (optional) short human-readable description of event
        :return: ID of this schedule
        """
        # FIXME: more users at once; better action parameter
        self._validate_user(user)
        self._validate_action(action)
        at = self._validate_datetime(at)
        schedule = ScheduledAction(_at=at, action=action, 
            description=description, users={"conversation_ids": [user]})
        schedule.save()
        task_id = "botshot_schedule_{}".format(schedule._id)
        MessageScheduler._create_schedule.delay(schedule._id)
        return task_id
    
    def add_recurrent_schedule(
        self, action, user: str, 
        hour, minute, day_of_week='*', day_of_month='*',
        month_of_year='*', until=None, description=None
    ) -> str:
        cron = {
            "hour": hour,
            "minute": minute,
            "day_of_week": day_of_week,
            "day_of_month": day_of_month,
            "month_of_year": month_of_year
        }
        self._validate_user(user)
        self._validate_cron(**cron)
        self._validate_action(action)
        until = self._validate_datetime(until)
        schedule = ScheduledAction(cron=cron, _until=until, 
            action=action, description=description, users={"conversation_ids": [user]})
        schedule.save()
        task_id = "botshot_schedule_{}".format(schedule._id)
        MessageScheduler._create_schedule.delay(schedule._id)
        return task_id

    def remove_schedule(self, schedule_id):
        if not schedule_id or not schedule_id.startswith("botshot_schedule_"):
            raise Exception("Invalid schedule ID")
        db_key = schedule_id[len("botshot_schedule_"):]
        schedule = ScheduledAction.objects.get(pk=db_key)
        schedule.delete()
        MessageScheduler._delete_schedule.delay(schedule_id)

    def list_schedules(self):
        return ScheduledAction.objects.all()

    # Warning: schedules shouldn't EVER be updated, 
    # otherwise - undefined behaviour

    @staticmethod
    @shared_task(bind=True, name="botshot.schedule_create")
    def _create_schedule(self, schedule_id):
        celery = self.app
        logging.debug("Creating schedule {}".format(schedule_id))
        model = ScheduledAction.objects.get(pk=schedule_id)
        task_id = "botshot_schedule_{}".format(model._id)

        if model.at and model.at > timezone.now():
            logging.debug("Creating one-time schedule at %s", str(model.at))
            MessageScheduler._schedule_wrapper.apply_async(
                (model.users, model.action,), task_id=task_id, eta=model.at)
        elif model.cron and (not model.until or model.until > timezone.now()):
            logging.debug("Creating repeating schedule")
            if model.until:
                # make sure that the event is removed at "until"
                MessageScheduler._delete_schedule.apply_async((schedule_id,), 
                    task_id=task_id+"_del", eta=model.until)
            # schedule the event itself
            celery.conf.beat_schedule[task_id] = {
                "task": "botshot.schedule_wrapper",
                "schedule": crontab(**model.cron),
                "args": (model.users, model.action,)
            }
        else:
            # schedule has expired
            logging.warning("Schedule called with past or no datetime, removing it")
            model.delete()

    @staticmethod
    @shared_task(bind=True, name="botshot.schedule_delete")
    def _delete_schedule(self, task_id):
        celery = self.app
        if 'task_id' in celery.conf.beat_schedule:
            del celery.conf.beat_schedule[task_id]
            celery.control.revoke(task_id+"_del", terminate=True)
        celery.control.revoke(task_id, terminate=True)

    @staticmethod
    @shared_task(name='botshot.schedule_wrapper', bind=True)
    def _schedule_wrapper(self, user_spec: dict, action, task_id=None):
        from botshot.core.chat_manager import ChatManager
        logging.debug("Running schedule %s", task_id)
        conversations = []
        if 'conversation_ids' in user_spec:
            conversations = user_spec['conversation_ids']
        elif 'filter' in user_spec:
            raise NotImplementedError()  # TODO
        elif 'all' in user_spec:
            raise NotImplementedError()  # TODO

        if isinstance(action, dict):
            # Botshot state + context schedule, different for each conversation
            manager = ChatManager()
            for id in conversations:
                manager.accept_scheduled(
                    conversation_id=id, user_id=None, payload=action)
        elif isinstance(action, MessageElement):
            # Prepared MessageElement schedule, sent as a broadcast
            # TODO: send the message to the interfaces
            # TODO: send more messages at once
            raise NotImplementedError()

    @staticmethod
    @beat_init.connect
    def on_schedule_reload(sender, **kwargs):
        for key in sender.app.conf.beat_schedule.keys():
            if key.startswith("botshot_schedule_"):
                del sender.app.conf.beat_schedule[key]
        for schedule in ScheduledAction.objects.all():
            MessageScheduler._create_schedule.delay(schedule._id)

    def _validate_cron(self, **kwargs):
        try:
            crontab(**kwargs)
        except Exception as e:
            raise Exception("Invalid schedule specification") from e

    def _validate_user(self, user):
        pass  # TODO

    def _validate_action(self, action):
        if not isinstance(action, dict) and not isinstance(action, MessageElement):
            raise Exception("Action parameter should be: "
                            "a) a dict with message payload, or "
                            "b) a MessageElement.")

    def _validate_datetime(self, dt):
        if dt is None or not isinstance(dt, datetime):
            raise Exception("Parameter must be instance of datetime.datetime")
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            raise Exception("Datetime must be tz-aware")
        return dt.astimezone(pytz.utc)  # this makes sure the database doesn't screw up
