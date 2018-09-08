import os
from celery import Celery

try:
    from botshot.tasks import *
except ModuleNotFoundError:
    print('Error: Unable to find botshot module.')
    print('If running in dev environment, create a link to the inner botshot directory using "ln -s ../path/to/botshot/botshot botshot".')
    exit(1)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bot.settings')

app = Celery('bot')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
