import re


class Entity:
    def __init__(self, name: str, value, raw, counter: int, scope=None, state=None):
        self.name = name
        self.value = value
        self.state = state
        self.scope = re.compile(scope) if scope else re.compile(".*")
        self.raw = raw or {}
        self._counter = counter

    def get_age(self, counter_now) -> int:
        return counter_now - self._counter

    def is_valid(self, state_name):
        return self.scope.match(state_name)

    def compare_age(self, entity):
        return self._counter - entity._counter

    def to_dict(self):
        return {
            "name": self.name,
            "value": self.value,
            "state": self.state,
            "scope": self.scope.pattern,
            "counter": self._counter,
            "raw": self.raw,
        }

    def __str__(self):
        import json
        return json.dumps(self.to_dict(), indent=2)

    @staticmethod
    def from_dict(data: dict):
        if isinstance(data, dict) and 'name' in data and 'value' in data:
            return Entity(
                name=data['name'], value=data['value'], counter=data.get('counter', 0),
                scope=data.get('scope'), state=data.get('state'), raw=data.get('raw')
            )
        print("Refusing to load empty entity!")
        return None


class EntityLocation(Entity):
    def __init__(self, name: str, value, raw, counter: int, scope=None, state=None):
        super(EntityLocation, self).__init__(name, value, raw, counter, scope, state)
        self.lat, self.lng = None, None ## FIXME !!!
        self.source = None
        self.accuracy = None
