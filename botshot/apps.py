from django.apps import AppConfig


class BotshotConfig(AppConfig):
    name = 'botshot'

    def ready(self):
        from botshot.core.flow import init_flows
        from botshot.core.logging import logging_service
        init_flows()
        logging_service.init()
