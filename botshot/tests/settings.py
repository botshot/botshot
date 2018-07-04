import os

BOT_CONFIG = {
    "REDIS": {
        "HOST": 'localhost',
        "PORT": 6379,
        "PASSWORD": None,
    },
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
    }
}

SECRET_KEY = "foo"
