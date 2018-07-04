import time


class EntityValue:
    """
    This class holds the value of a single entity in context.
    """

    def __init__(self, context, name, value=None, raw=None):
        self.name = name
        self.raw = raw or dict()  # type: dict
        self.value = value or self.raw.get("value")
        self.timestamp = time.time()
        self.counter = context.counter
        self.state_set = context.get_state_name() or ""

    # Methods to access the raw data returned by parsers

    def get(self, key, default=None):
        return self.raw.get(key, default)

    def __contains__(self, item):
        return self.raw.__contains__(item)

    def __getitem__(self, item):
        return self.raw.__getitem__(item)

    # Common methods to access values

    def __str__(self):
        return self.value

    def __repr__(self):
        return "EntityValue:" + str(self.value)
