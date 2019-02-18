import time


class EntityValue:
    """
    This class holds the value of a single entity in context.
    """

    def __init__(self, name, counter, state_set, value=None, raw=None, role=None, timestamp=None):
        self.name = name
        self.raw = raw or dict()  # type: dict
        self.value = value or self.raw.get("value")
        self.role = role or self.raw.get("role")
        self.timestamp = timestamp or time.time()
        self.counter = counter
        self.state_set = state_set or ""

    # Methods to access the raw data returned by parsers

    def get(self, key, default=None):
        return self.raw.get(key, default)

    def __contains__(self, item):
        return self.raw.__contains__(item)

    def __getitem__(self, item):
        return self.raw.__getitem__(item)

    # Common methods to access values

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return "EntityValue:" + str(self.value)
