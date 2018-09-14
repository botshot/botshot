from django.apps import AppConfig


class BotshotConfig(AppConfig):
    name = 'botshot'

    def ready(self):
        from botshot.core.interfaces import init_webhooks
        from botshot.core.flow import init_flows
        from botshot.core.logging import logging_service
        init_webhooks()
        init_flows()
        logging_service.init()
        # TODO skip webhooks if just running task like django migrate
        print("Initializing webhooks ...")
        init_webhooks()
