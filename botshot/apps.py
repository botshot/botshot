from django.apps import AppConfig


class BotshotConfig(AppConfig):
    name = 'botshot'

    def ready(self):
        from botshot.core.interface_factory import InterfaceFactory
        import botshot.core.scheduler  # loads periodic scheduler task
        interfaces = InterfaceFactory().get_interfaces()
        for itf in interfaces:
            itf().on_server_startup()
