import logging

import requests

from botshot.core import config
from botshot.core.parsing import EntityExtractor
from requests import HTTPError


class BotshotRemoteNLU(EntityExtractor):

    def __init__(self):
        super().__init__()
        self.url = config.get("REMOTE_NLU_URL")
        self.default_locale = "en_US"
        if not self.url:
            logging.error("Remote NLU URL not provided. NLU will not work.")

    def extract_entities(self, text: str, max_retries=1, locale=None, **kwargs):
        if not text:
            return {}
        for i in range(max_retries):
            try:
                return self._parse_request(text, locale)
            except HTTPError:
                logging.exception("Exception in Botshot NLU request")

    def _parse_request(self, text, locale=None):
        payload = {
            "text": text,
            "locale": locale or self.default_locale,
        }
        resp = requests.get(self.url + '/parse', params=payload)
        resp.raise_for_status()
        return resp.json()


class MultilanguageRouter(EntityExtractor):

    def __init__(self):
        super().__init__()
        self.languages = config.get_required("NLU_LANGUAGES",
                                             "Please provide a dict of 'locale': 'url' in config/NLU_LANGUAGES.")
        if not isinstance(self.languages, dict) or 'default' not in self.languages:
            raise Exception("Please provide a default extractor in NLU_LANGUAGES.")

    def extract_entities(self, text: str, max_retries=1, locale=None, **kwargs):
        if locale not in self.languages:
            locale = 'default'
        base_url = self.languages[locale]
        if not text:
            return {}
        for i in range(max_retries):
            try:
                return self._parse_request(base_url, text, locale)
            except HTTPError:
                logging.exception("Exception in Botshot NLU request")

    def _parse_request(self, base_url, text, locale):
        payload = {
            "text": text,
            "locale": locale,
        }
        resp = requests.get(base_url + '/parse', params=payload)
        resp.raise_for_status()
        return resp.json()


class BotshotExtractor(EntityExtractor):

    def __init__(self):
        super().__init__()
        self.nlu = None

    def extract_entities(self, text: str, max_retries=1, locale=None, **kwargs):
        if not self.nlu:
            from botshot.nlu.predict import BotshotNLU
            self.nlu = BotshotNLU.load()
            global BOTSHOT_NLU
            BOTSHOT_NLU = self.nlu

        # TODO use a separate thread (pool) to remove TF memory overhead
        return self.nlu.parse(text)


BOTSHOT_NLU = None
