import os.path

STATICFILES_DIRS = (
    os.path.join(os.path.dirname(__file__), 'static')
)
MIDLLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware'
]
