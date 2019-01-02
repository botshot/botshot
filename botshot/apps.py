from django.apps import AppConfig


class BotshotConfig(AppConfig):
    name = 'botshot'

    def ready(self):
        from botshot.core.flow import init_flows
        from botshot.core.interface_factory import InterfaceFactory
        init_flows()  # TODO: improve flows initialization
        interfaces = InterfaceFactory().get_interfaces()
        for itf in interfaces:
            itf().on_server_startup()
