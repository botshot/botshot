import logging

from celery.schedules import crontab
from celery import shared_task
from celery.signals import beat_init

from datetime import datetime
from botshot.models import ScheduledAction
from django.db.models.signals import post_save, post_delete


class MessageScheduler:

    def add_schedule(self, action: str, at: datetime, description=None) -> str:
        if not isinstance(at, datetime):
            raise Exception("At parameter should be datetime.datetime")
        if not isinstance(action, str):
            raise Exception("Action parameter should be a string containing state name")
        schedule = ScheduledAction(at=at, action=action, description=description)
        schedule.save()
        task_id = "botshot_schedule_{}".format(schedule._id)
        return task_id
    
    def add_recurrent_schedule(
        self, action: str, hour, minute,
        day_of_week='*', day_of_month='*',
        month_of_year='*', until=None, description=None
    ) -> str:
        cron = {
            "hour": hour,
            "minute": minute,
            "day_of_week": day_of_week,
            "day_of_month": day_of_month,
            "month_of_year": month_of_year
        }
        self._validate_cron(**cron)
        if until is not None and not isinstance(until, datetime):
            raise Exception("Until parameter should be datetime.datetime")
        if not isinstance(action, str):
            raise Exception("Action parameter should be a string containing state name")
        schedule = ScheduledAction(cron=cron, until=until, action=action, description=description)
        schedule.save()
        task_id = "botshot_schedule_{}".format(schedule._id)
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
    def on_schedule_updated(sender, **kwargs):
        schedule = kwargs.get('instance')
        MessageScheduler._create_schedule.delay(schedule.pk)

    @staticmethod
    def on_schedule_deleted(sender, **kwargs):
        schedule = kwargs.get('instance')
        MessageScheduler._delete_schedule.delay(schedule.pk)

    @staticmethod
    @shared_task(bind=True, name="botshot.schedule_create")
    def _create_schedule(self, schedule_id):
        celery = self.app
        logging.debug("Creating schedule {}".format(schedule_id))
        model = ScheduledAction.objects.get(pk=schedule_id)
        task_id = "botshot_schedule_{}".format(model._id)

        if 'task_id' in celery.conf.beat_schedule:
            del celery.conf.beat_schedule[task_id]
            celery.control.revoke(task_id+"_del", terminate=True)
        celery.control.revoke(task_id, terminate=True)

        if model.at and model.at > datetime.now().time():
            logging.debug("Creating one-time schedule")
            MessageScheduler._schedule_wrapper.apply_async(
                (model.action,), task_id=task_id, eta=model.at)
        elif model.cron and (not model.until or model.until > datetime.now()):
            logging.debug("Creating repeating schedule")
            # make sure that the event is removed at "until"
            MessageScheduler._delete_schedule.apply_async((schedule_id,), 
                task_id=task_id+"_del", eta=model.at)
            # schedule the event itself
            celery.conf.beat_schedule[task_id] = {
                "task": "botshot.schedule_wrapper",
                "schedule": crontab(**model.cron),
                "args": (model.action,)
            }
        else:
            # schedule has expired
            model.delete()

    @staticmethod
    @shared_task(bind=True, name="botshot.schedule_delete")
    def _delete_schedule(self, schedule_id):
        celery = self.app
        task_id = "botshot_schedule_{}".format(schedule_id)
        if 'task_id' in celery.conf.beat_schedule:
            del celery.conf.beat_schedule[task_id]
            celery.control.revoke(task_id+"_del", terminate=True)
        celery.control.revoke(task_id, terminate=True)

    @staticmethod
    @shared_task(name='botshot.schedule_wrapper')  # TODO: discover
    def _schedule_wrapper(action):
        import logging
        print("Action (1):", action)
        logging.error("Action (2): {}".format(action))

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


post_save.connect(MessageScheduler.on_schedule_updated, sender=ScheduledAction)
post_delete.connect(MessageScheduler.on_schedule_deleted, sender=ScheduledAction)
