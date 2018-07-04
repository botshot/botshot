from django.apps import AppConfig


class BotshotConfig(AppConfig):
    name = 'botshot'

    def ready(self):
        print('Init webhooks @ BotshotConfig')
        from botshot.core.interfaces.all import init_webhooks
        init_webhooks()
