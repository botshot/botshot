import logging
import time
from typing import Union

from collections import Iterable
from functools import reduce

from botshot.core.entity_query import EntityQuery
from botshot.core.entity_value import EntityValue


class Context(object):

    def __init__(self, dialog, entities, history, counter, max_depth=30, history_restart_minutes=30):
        self.counter = counter
        self.entities = entities
        self.history = history
        self.max_depth = max_depth
        self.dialog = dialog
        self.history_restart_minutes = history_restart_minutes

    def __getattr__(self, item):
        if item in ['counter', 'entities', 'history', 'max_depth', 'dialog', 'history_restart_minutes']:
            return super().__getattribute__(item)
        return self.__getitem__(item)

    def __setattr__(self, key, value):
        if key in ['counter', 'entities', 'history', 'max_depth', 'dialog', 'history_restart_minutes']:
            return super().__setattr__(key, value)
        return self.__setitem__(key, value)

    def __contains__(self, key: Union[str, Iterable]):
        if isinstance(key, str):
            return key in self.entities and self.entities[key]
        elif isinstance(key, Iterable):
            return reduce(lambda x, y: x and y, map(self.__contains__, key))
        raise ValueError("Argument must be either entity name (str) or an iterable of entity names")

    def to_dict(self):
        return {
            'history': self.history,
            'entities': self.entities,
            'counter': self.counter,
        }

    @staticmethod
    def from_dict(dialog, data):
        history = data.get("history", [])
        counter = int(data.get("counter", 0))
        entities = data.get("entities", {})
        return Context(dialog=dialog, entities=entities, history=history, counter=counter)

    def add_message_entities(self, entities):
        # TODO don't increment when @ requires -> input and it's valid
        # TODO what to say and do on invalid requires -> input?
        self.counter += 1
        for entity_name, entity_values in entities.items():
            # allow also direct passing of {'entity' : 'value'}

            if not isinstance(entity_values, dict) and not isinstance(entity_values, list):
                entity_values = {'value': entity_values}
            if not isinstance(entity_values, list):
                entity_values = [entity_values]

            # FIXME use a factory to build the correct subclass with right arguments
            # prepend each value to start of the list with 0 age
            for value in entity_values:
                self.add_entity_dict(entity_name, value)

    def add_entity_dict(self, entity_name, entity_dict):

        if 'value' in entity_dict:
            entity = EntityValue(entity_name, counter=self.counter, state_set=self.get_state_name(), raw=entity_dict)
            self.entities.setdefault(entity_name, []).insert(0, entity)

        if 'values' in entity_dict:  # compound entities (probably Wit.ai?)
            for item in entity_dict['values']:
                for role, entity in item.items():
                    canon_name = entity_name + "__" + role
                    entity = EntityValue(canon_name, counter=self.counter, state_set=self.get_state_name(), value=entity)
                    self.entities.setdefault(canon_name, []).insert(0, entity)

    def add_state(self, state_name):
        timestamp = int(time.time())
        if len(self.history) > 20:
            self.history = self.history[-20:]

        state = {
            'name': state_name,
            'timestamp': timestamp
        }
        self.history.append(state)

    def clear(self, entities):
        for entity in entities:
            if entity in self.entities:
                del self.entities[entity]

    def get_min_entity_age(self, entities):
        ages = [self.get_age(entity)[1] for entity in entities]
        ages = filter(lambda x: x is not None, ages)
        return min(ages) if ages else None

    def get_history_state(self, index):
        if index < 0:
            index = len(self.history) - index
        return self.history[index] if len(self.history) > index >= 0 else None

    def get_state_name(self):
        return ""  # FIXME: self.dialog.current_state_name
        # return self.history[-1] if len(self.history) > 0 else None

    def get_all(self, entity, max_age=None, limit=None, ignored_values=None) -> list:
        values = []
        if entity not in self.entities:
            return values
        for entity_obj in self.entities[entity]:  # type: EntityValue
            age = self.counter - entity_obj.counter
            # if I found a too old value, stop looking
            if max_age is not None and age > max_age:
                break
            v = entity_obj.value
            if ignored_values and v in ignored_values:
                logging.info('Skipping ignored entity value: {} == {}'.format(entity, v))
                continue

            values.append(entity_obj)
            # if I already have enough values, stop looking
            if limit is not None and len(values) >= limit:
                break
        return values
    
    def debug(self, max_age=5, level=logging.INFO):
        logging.log(level, '-- HEAD of Context (max age {}): --'.format(max_age))
        for entity in self.entities:
            entities = self.get_all_first(entity, max_age=max_age)
            if entities:
                vs = [entity.value for entity in entities]
                logging.log(level, '{} (age {}): {}'.format(entity, self.counter - entities[0].counter, vs if len(vs) > 1 else vs[0]))
        logging.log(level, '----------------------------------')

    def get(self, entity, max_age=None, ignored_values=None) -> EntityValue or None:
        values = self.get_all(entity, max_age=max_age, limit=1, ignored_values=ignored_values)
        if not values:
            return None
        return values[0]

    def get_value(self, entity, max_age=None, ignored_values=None) -> object:
        values = self.get_all(entity, max_age=max_age, limit=1, ignored_values=ignored_values)
        if not values:
            return None
        return values[0].value

    def get_age(self, entity, max_age=None, ignored_values=None):
        ents = self.get_all(entity, max_age=max_age, limit=1, ignored_values=ignored_values)
        if not ents:
            return None, None
        return ents[0], (self.counter - ents[0].counter)

    def get_all_first(self, entity_name, max_age=None):
        values = []
        if entity_name not in self.entities:
            return values
        found_age = None
        existing = []
        for entity_obj in self.entities[entity_name]:  # type: EntityValue
            age = self.counter - entity_obj.counter
            # if I found a too old value, stop looking
            if max_age is not None and age > max_age:
                break
            if found_age is not None and age > found_age:
                break
            found_age = age
            if entity_obj.value in existing:
                # skip duplicates
                continue
            existing.append(entity_obj.value)
            values.append(entity_obj)
        return values[::-1]

    def set(self, entity_name, value_dict):
        if not isinstance(value_dict, dict):
            raise ValueError('Use a dict to set a context value, e.g. {"value":"foo"}. Call multiple times to add more.')
        value_dict['counter'] = self.counter
        entity_obj = EntityValue(entity_name, counter=self.counter, state_set=self.get_state_name(), raw=value_dict)
        self.entities.setdefault(entity_name, []).insert(0, entity_obj)
        self.entities[entity_name] = self.entities[entity_name][:self.max_depth - 1]

    def set_value(self, entity_name, value):
        entity_obj = EntityValue(entity_name, counter=self.counter, state_set=self.get_state_name(), value=value)
        self.entities.setdefault(entity_name, []).insert(0, entity_obj)
        self.entities[entity_name] = self.entities[entity_name][:self.max_depth - 1]

    def has_any(self, entities, max_age=None):  # TODO
        for entity in entities:
            if self.get(entity, max_age=max_age):
                return True
        return False

    def has_all(self, entities, max_age=None):  # TODO
        for entity in entities:
            if not self.get(entity, max_age=max_age):
                return False
        return True

    def __getitem__(self, item):
        return EntityQuery(self, item, self.entities.get(item, []))

    def __setitem__(self, key, value):
        if not isinstance(value, EntityValue):
            value = EntityValue(key, counter=self.counter, state_set=self.get_state_name(), value=value)
        self.entities.setdefault(key, []).insert(0, value)
        return self.__getitem__(key)  # mainly to shut up IDE warnings
