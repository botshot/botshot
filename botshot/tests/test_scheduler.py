import pytest
import mock
from django.utils import timezone


@pytest.fixture
def scheduler(monkeypatch):
    monkeypatch.setattr("celery.current_app", mock.Mock())
    from botshot.core.scheduler import MessageScheduler
    yield MessageScheduler()


@pytest.mark.django_db
class TestScheduler():

    def test_validate_conversation_filter(self, scheduler):
        filter = scheduler._validate_conversation_filter(105)
        assert filter.get_ids() == [105]
        filter = scheduler._validate_conversation_filter([105, 210, 420])
        assert filter.get_ids() == [105, 210, 420]

    def test_validate_timespec(self, scheduler):
        scheduler._validate_timespec({"second": 0})
        scheduler._validate_timespec({"second": 1})
        scheduler._validate_timespec({"second": 0, "minute": 0})
        scheduler._validate_timespec({"second": 1, "minute": 1, "hour": 0})
        scheduler._validate_timespec({"second": 1, "minute": 1, "hour": 0, "day_of_week": 1})
        scheduler._validate_timespec({"second": 1, "minute": 1, "hour": 0, "day_of_month": 1})
        scheduler._validate_timespec({"second": 1, "minute": 1, "hour": 0, "day_of_month": 1, "month_of_year": 1})

        with pytest.raises(Exception):
            scheduler._validate_timespec({"second": -1})
        with pytest.raises(Exception):
            scheduler._validate_timespec({"second": 'a'})
        with pytest.raises(Exception):
            scheduler._validate_timespec({"second": -1e5})
        with pytest.raises(Exception):
            scheduler._validate_timespec({"second": None})
        with pytest.raises(Exception):
            scheduler._validate_timespec({"hour": 32})
        with pytest.raises(Exception):
            scheduler._validate_timespec({})
        with pytest.raises(Exception):
            scheduler._validate_timespec({"minute": 1, "hour": 0, "day_of_week": 1, "day_of_month": 1})
        with pytest.raises(Exception):
            scheduler._validate_timespec({"second": 1, "minute": 1, "hour": 0, "month_of_year": 1})

    def test_add_schedule(self, scheduler):
        action = {"_state": "foo.bar:"}
        conversations = [105, 106]
        at = timezone.now()
        description = "Hello world!"
        task_id = scheduler.add_schedule(action, conversations, at, description)
        from botshot.models import ScheduledAction
        from botshot.core.persistence import json_deserialize
        pk = task_id.split("botshot_schedule_")[1]
        s = ScheduledAction.objects.get(pk=pk)
        assert s.conversations.get_ids() == scheduler._validate_conversation_filter(conversations).get_ids()
