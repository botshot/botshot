from botshot.core.interfaces import BotshotInterface
from botshot.core import config
from django.utils.module_loading import import_string


class InterfaceFactory:

    @staticmethod
    def from_name(name) -> BotshotInterface:
        for interface_class in InterfaceFactory.get_interfaces():
            if interface_class.name == name:
                return interface_class()
        raise ValueError("Unknown interface name '{}'. Did you register the class in INTERFACES config property?".format(name))

    @staticmethod
    def get_interfaces():
        interface_paths = config.get_required('INTERFACES')
        return [import_string(path) for path in interface_paths]