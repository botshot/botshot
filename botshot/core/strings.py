import logging
import os
import csv

from abc import ABC, abstractmethod

from botshot.core import config

DELIMITER = '\t'


class StringLoader(ABC):

    def __init__(self, locale='en_US'):
        self.locale = locale

    def get(self, key: str, *args, **kwargs):
        """
        Loads a string by its key, optionally formatting it.

        :param key:     key (ID) of the string to retrieve
        :param args:    python string format args
        :param kwargs:  python string format kwargs
        :returns:       localized string or None if not found
        """
        value = self._get(key)
        if value and (args or kwargs):
            value = value.format(*args, **kwargs)
        return value

    def set_locale(self, locale):
        self.locale = locale

    def __getitem__(self, key: str):
        return self._get(key)

    @abstractmethod
    def _get(self, key: str):
        raise NotImplementedError()


class SimpleStringLoader(StringLoader):

    def __init__(self, locale='en_US'):
        super().__init__(locale)
        self.strings = {}

        string_files = config.get("STRING_FILES")
        if not string_files:
            logging.debug("STRING_FILES not set. Strings will not be available.")
        for lang, filename in string_files.items():
            self.strings[lang] = self._load_strings(filename)

    def _load_strings(self, filename):
        strings = {}
        with open(filename) as fp:
            reader = csv.reader(fp, delimiter=DELIMITER)
            for row in reader:
                if len(row) <= 0 or row[0].lstrip().startswith("#"):
                    continue  # empty line or comment
                key, value = row[0], DELIMITER.join(row[1:])
                value = value.replace(r"\n", "\n")
                strings[key] = value
        return strings

    def _get(self, key: str):
        localized = self.strings.get(self.locale, {})
        return localized.get(key)
