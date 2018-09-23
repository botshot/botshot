from django.conf import settings


def get_required(field, error_message=None):
    value = settings.BOT_CONFIG.get(field)
    if value is None:
        raise KeyError(error_message or "Missing required botshot config property: '{}'".format(field))
    return value


def get(field, default=None):
    return settings.BOT_CONFIG.get(field, default)
