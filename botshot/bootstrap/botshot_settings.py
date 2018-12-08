STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(STATIC_ROOT, 'media')

BOT_CONFIG = {
    "BOTS": {
        "bot/bots/default.yaml"
    },
    "INTERFACES": [
        'botshot.webchat.interface.WebchatInterface',
        'botshot.core.interfaces.MessengerInterface'
    ],
    # Change this secret url to hide your public webhooks!
    "WEBHOOK_SECRET_URL": "8gu20xksls94udjv840f1",
    "REDIS_URL": os.environ.get('BOTSHOT_REDIS_URL', "redis://localhost:6379/"),
    'DEPLOY_URL': os.environ.get('BOTSHOT_DEPLOY_URL', 'http://localhost:8000/'),
    'MSG_LIMIT_SECONDS': 20,
    'MESSAGE_LOGGERS': []
}

CELERY_BROKER_URL = BOT_CONFIG.get('REDIS_URL')+'/1'
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['pickle']
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'