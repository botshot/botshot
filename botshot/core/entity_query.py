import time

import re
from typing import Optional

from botshot.core.entity_value import EntityValue


class EntityQuery:
    def __init__(self, context, name, items):
        self.context = context
        self.name = name or ""
        self.items = items or []

    # TODO filter by roles

    def newer_than(self, messages=None, delta=None, abs_time=None):
        """
        Filter to all entities that are newer than ...
        :param messages
        :param delta
        :param abs_time
        :return: self
        """
        if (messages is not None and (delta is not None or abs_time is not None)) \
                or (delta is not None and abs_time is not None):
            raise ValueError("Please use either message count, timedelta or absolute time")
        if messages is not None:
            counter_now = self.context.counter
            self.items = filter(lambda x: counter_now - x.counter < messages, self.items)
        elif delta is not None:
            time_min = time.time() - delta.total_seconds()
            self.items = filter(lambda x: x.timestamp > time_min, self.items)
        elif abs_time is not None:
            self.items = filter(lambda x: x.timestamp > abs_time, self.items)
        self.items = list(self.items)
        return self

    def older_than(self, messages=None, delta=None, abs_time=None):
        """
        Filter to all entities that are older than ...
        :param messages
        :param delta
        :param abs_time
        :return: self
        """
        if (messages is not None and (delta is not None or abs_time is not None)) \
                or (delta is not None and abs_time is not None):
            raise ValueError("Please use either message count, timedelta or absolute time")
        if messages is not None:
            counter_now = self.context.counter
            self.items = filter(lambda x: counter_now - x.counter > messages, self.items)
        elif delta is not None:
            time_max = time.time() - delta.total_seconds()
            self.items = filter(lambda x: x.timestamp < time_max, self.items)
        elif abs_time is not None:
            self.items = filter(lambda x: x.timestamp < abs_time, self.items)
        self.items = list(self.items)
        return self

    def exactly(self, messages=None, delta=None, abs_time=None):
        """
        Filter to all entities that occurred exactly at ...
        :param messages
        :param delta
        :param abs_time
        :return: self
        """
        if (messages is not None and (delta is not None or abs_time is not None)) \
                or (delta is not None and abs_time is not None):
            raise ValueError("Please use either message count, timedelta or absolute time")
        if messages is not None:
            counter_now = self.context.counter
            self.items = filter(lambda x: counter_now - x.counter == messages, self.items)
        elif delta is not None:
            time_max = time.time() - delta.total_seconds()
            self.items = filter(lambda x: abs(x.timestamp - time_max) < 1.0, self.items)
        elif abs_time is not None:
            self.items = filter(lambda x: abs(x.timestamp - abs_time) < 1.0, self.items)
        self.items = list(self.items)
        return self

    def include_flow(self, regex: str):
        """Include just entities that were set in a state that matches the regex."""
        self.items = list(filter(lambda x: re.match(regex, x.state_set), self.items))
        return self

    def exclude_flow(self, regex: str):
        """Exclude all entities that were set in a state that matches the regex."""
        self.items = list(filter(lambda x: re.match(regex, x.state_set) is None, self.items))
        return self

    def set_with(self, entity: str, value):
        # FIXME make lookups by age effective
        filtered = []
        for item in self.items:
            counter = item.counter
            entity_arr = self.context.entities.get(entity, [])
            for entity in entity_arr:
                if entity.counter == counter and entity.value == value:
                    filtered.append(item)
                    break
        self.items = filtered
        return self

    def not_set_with(self, entity: str, value):
        # FIXME make lookups by age effective
        filtered = []
        for item in self.items:
            counter = item.counter
            entity_arr = self.context.entities.get(entity, [])
            has_match = False
            for entity in entity_arr:
                if entity.counter == counter and entity.value == value:
                    has_match = True
                    break
            if not has_match:
                filtered.append(entity)
        self.items = filtered
        return self

    def get(self, this_msg=False) -> Optional[EntityValue]:
        """
        Returns the newest entity in context.
        You can limit search to the newest message from user by setting this_msg to True.

        :param this_msg: True to search only in last received message
        :return: Instance of EntityValue or None.
        """
        item = self.items[0] if len(self.items) else None

        if this_msg and (item is not None) and (item.counter != self.context.counter):
            return None

        return item

    def get_value(self, this_msg=False) -> Optional[object]:
        """
        Returns value of the newest entity in context.
        You can limit search to the newest message from user by setting this_msg to True.

        :param this_msg: True to search only in last received message
        :return: Value of newest entity or None.
        """
        item = self.get(this_msg=this_msg)
        return item.value if item else None

    def get_age(self) -> int:
        """Returns age of the latest entity in messages, or -1 if there are no entities."""
        self.items = sorted(self.items, key=lambda x: x.timestamp, reverse=True)
        return (self.items[0].counter - self.context.counter) if len(self.items) > 0 else -1

    def values(self):
        """Returns a list with values of all present entities."""
        return [x.value for x in self]

    def count(self):
        return len(self.items)

    def __nonzero__(self):
        return self.count() > 0

    def __or__(self, other):
        # WARNING: This method allows you to mix up arbitrary entities and EntityValue subclasses!
        if not isinstance(other, EntityQuery):
            raise ValueError("OR operator argument must be an EntityQuery")
        elif self.context != other.context:
            raise ValueError("Refusing to do OR operation, other query's context is not the same")

        new_name = '|'.join([self.name, other.name])
        new_items = set(self.items).union(other.items)
        return EntityQuery(self.context, new_name, new_items)

    def __and__(self, other):
        if not isinstance(other, EntityQuery):
            raise ValueError("AND operator argument must be an EntityQuery")
        elif self.context != other.context:
            raise ValueError("Refusing to do OR operation, other query's context is not the same")

        new_items = set(self.items).intersection(set(other.items))
        return EntityQuery(self.context, self.name, new_items)

    def __iter__(self):
        return iter(list(self.items))

    def __getitem__(self, idx: int):
        if idx < 0 or idx > len(self.items):
            raise ValueError("Entity index out of bounds")
        return self.items[idx]

    def __len__(self):
        return len(self.items)

    @staticmethod
    def from_yaml(context, name: str, yml: list):
        # TODO catch and log errors
        eq = EntityQuery(context, name, context.entities.get(name, []))
        for item in yml:
            key, values = list(item.items())[0]
            if key == 'or':
                or_eq = None
                for arg in values:
                    if not isinstance(arg, list):
                        arg = [arg]
                    if or_eq:
                        or_eq = or_eq.__or__(EntityQuery.from_yaml(context, name, arg))
                    else:
                        or_eq = EntityQuery.from_yaml(context, name, arg)
                eq = eq and or_eq
            elif key == 'set-with':
                entity, value = values.split(', ', maxsplit=1)
                eq.set_with(entity, value)
            elif key == 'not-set-with':
                entity, value = values.split(', ', maxsplit=1)
                eq.not_set_with(entity, value)
            elif key == 'include-flow':
                flow = values
                eq.include_flow(flow)
            elif key == 'exclude-flow':
                flow = values
                eq.exclude_flow(flow)
            elif key == 'newer':
                raise NotImplementedError("TO DO")
            elif key == 'older':
                raise NotImplementedError("TO DO")
            elif key == 'exactly':
                raise NotImplementedError("TO DO")
        return eq


class MockQuery(EntityQuery):
    pass  # TODO for testing
