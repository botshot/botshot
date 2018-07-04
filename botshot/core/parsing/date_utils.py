import datetime
from datetime import timedelta

import dateutil.parser
import pytz
from celery.utils.log import get_task_logger
from dateutil.relativedelta import relativedelta
from django.utils import timezone

logger = get_task_logger(__name__)


# TODO i18n


def process_datetime(values, duration=None):
    """
    Output example:
        Q: next_week: (datetime.datetime(2016, 11, 21, 0, 0, tzinfo=tzoffset(None, 3600)), datetime.datetime(2016, 11, 28, 0, 0, tzinfo=tzoffset(None, 3600)))
        Q: tomorrow: (datetime.datetime(2016, 11, 18, 0, 0, tzinfo=tzoffset(None, 3600)), datetime.datetime(2016, 11, 19, 0, 0, tzinfo=tzoffset(None, 3600)))
        Q: tonight: (datetime.datetime(2016, 11, 17, 18, 0, tzinfo=tzoffset(None, 3600)), datetime.datetime(2016, 11, 18, 0, 0, tzinfo=tzoffset(None, 3600)))
        Q: at weekend: (datetime.datetime(2016, 11, 18, 18, 0, tzinfo=tzoffset(None, 3600)), datetime.datetime(2016, 11, 21, 0, 0, tzinfo=tzoffset(None, 3600)))
    """

    append = {'date_interval': []}
    for value in values:
        try:
            formatted = None
            if value['type'] == 'interval':
                if 'from' not in value:  # default interval start is now
                    date_from = datetime.datetime.now().replace(tzinfo=pytz.timezone('Europe/Prague'))
                else:
                    date_from = dateutil.parser.parse(value['from']['value'])
                date_to = dateutil.parser.parse(value['to']['value']) - timedelta(seconds=1)
                grain = value['from']['grain']
            else:
                grain = value['grain']
                date_from = dateutil.parser.parse(value['value'])
                if grain == 'week' and date_from == date_this_week(date_from.tzinfo):
                    # change "this week" to next 7 days
                    date_from = timezone.now()
                    formatted = 'the next seven days'
                date_to = date_from + timedelta_from_grain(grain)
                if 'datetime' not in append:
                    append['datetime'] = []
                append['datetime'].append({'value': date_from, 'grain': grain})
            if not formatted:
                formatted = format_date_interval(date_from, date_to, grain)
            append['date_interval'].append({'value': (date_from, date_to), 'grain': grain, 'formatted': formatted})
        except ValueError:
            logger.exception('Error parsing date: {}'.format(value))
    return append


def timedelta_from_grain(grain):
    if grain == 'second':
        return timedelta(seconds=1)
    if grain == 'minute':
        return timedelta(minutes=1)
    if grain == 'hour':
        return timedelta(hours=1)
    if grain == 'day':
        return timedelta(days=1)
    if grain == 'week':
        return timedelta(days=7)
    if grain == 'month':
        return timedelta(days=31)
    if grain == 'year':
        return timedelta(days=365)
    return timedelta(days=1)


def date_now(tzinfo):
    return datetime.datetime.now(tzinfo)


def date_today(tzinfo):
    return date_now(tzinfo).replace(hour=0, minute=0, second=0, microsecond=0)


def date_this_week(tzinfo):
    today = date_today(tzinfo)
    return today - timedelta(days=today.weekday())


def date_this_month(tzinfo):
    today = date_today(tzinfo)
    return today - timedelta(days=today.day - 1)


def format_date_interval(from_date, to_date, grain):
    tzinfo = from_date.tzinfo
    now = date_now(tzinfo)
    today = date_today(tzinfo)
    this_week = date_this_week(tzinfo)
    next_week = this_week + timedelta(days=7)
    this_month = date_this_month(tzinfo)
    next_month = date_this_month(tzinfo) + relativedelta(months=1)

    diff_hours = (to_date - from_date).total_seconds() / 3600
    logger.info('Diff hours: %s' % diff_hours)

    if grain in ['second', 'minute'] and (now - from_date).total_seconds() < 60 * 5:
        return 'now'

    for i in range(0, 6):
        # if the dates are within the i-th day
        if from_date >= today + timedelta(days=i) and to_date <= today + timedelta(days=i + 1):
            if i == 0:
                day = 'today'
            elif i == 1:
                day = 'tomorrow'
            else:
                day = '%s' % from_date.strftime("%A")
            if from_date.hour >= 17:
                return 'this evening' if i == 0 else day + ' evening'
            if from_date.hour >= 12:
                return 'this afternoon' if i == 0 else day + ' afternoon'
            if to_date.hour >= 0 and to_date.hour < 13 and to_date.hour > 0:
                return 'this morning' if i == 0 else day + ' morning'
            return day

    if from_date == this_week and to_date == next_week:
        return 'this week'

    if from_date == next_week and to_date == next_week + timedelta(days=7):
        return 'next week'

    if from_date == this_month and to_date == next_month:
        return 'this month'

    if diff_hours <= 25:  # (25 to incorporate possible time change)
        digit = from_date.day % 10
        date = 'the {}{}'.format(from_date.day, 'st' if digit == 1 else ('nd' if digit == 2 else 'th'))
        return date if from_date.month == now.month else date + ' ' + from_date.strftime('%B')
    return 'these dates'
