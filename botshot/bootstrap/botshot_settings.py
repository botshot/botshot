STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(STATIC_ROOT, 'media')

BOT_CONFIG = {
    "BOTS": {
        "bot/bots/default.yaml"
    },
    "INTERFACES": [
        'botshot.webchat.interface.WebchatInterface',
        'botshot.core.interfaces.facebook.FacebookInterface',
    ],
    # Change this secret url to hide your public webhooks!
    "WEBHOOK_SECRET_URL": "8gu20xksls94udjv840f1",
    "FB_VERIFY_TOKEN": "INSERT_YOUR_VERIFY_TOKEN",
    "FB_PAGES": [{
        "NAME": "INSERT_YOUR_FB_PAGE_NAME",
        "TOKEN": "INSERT_YOUR_FB_PAGE_TOKEN",
    }],
    "MESSAGE_BROKER_URL": os.environ.get('MESSAGE_BROKER_URL', "redis://localhost:6379/1"),
    'DEPLOY_URL': os.environ.get('BOTSHOT_DEPLOY_URL', 'http://localhost:8000/'),
    'MSG_LIMIT_SECONDS': 20,
    'MESSAGE_LOGGERS': []
}

CELERY_BROKER_URL = BOT_CONFIG['MESSAGE_BROKER_URL']
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['pickle']
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'