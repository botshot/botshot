from django.apps import AppConfig


class BotshotConfig(AppConfig):
    name = 'botshot'

    def ready(self):
        from botshot.core.logging import logging_service
        logging_service.init()
        # TODO skip webhooks if just running task like django migrate
        print("Initializing webhooks ...")
        from botshot.core.interfaces import init_webhooks
        init_webhooks()
