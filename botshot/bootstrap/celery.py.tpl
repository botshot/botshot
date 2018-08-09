import os
from celery import Celery

try:
    from botshot.tasks import *
except ModuleNotFoundError:
    print('Error: Unable to find botshot module.')
    print('If running in dev environment, create a link to the inner botshot directory using "ln -s ../path/to/botshot/botshot botshot".')
    exit(1)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bot.settings')

redis_url = settings.CELERY_BROKER_URL

app = Celery('bot', backend='redis', broker=redis_url)
app.conf.update(BROKER_URL=redis_url,
                CELERY_RESULT_BACKEND=redis_url)

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
