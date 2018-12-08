import logging

import requests
from django.conf import settings

from botshot.core.parsing.entity_extractor import EntityExtractor
from requests import HTTPError


class BotshotRemoteNLU(EntityExtractor):

    def __init__(self):
        super().__init__()
        self.url = settings.BOT_CONFIG.get("REMOTE_NLU_URL")
        if not self.url:
            logging.error("Remote NLU URL not provided. NLU will not work.")

    def extract_entities(self, text: str, max_retries=1):
        for i in range(max_retries):
            try:
                return self._parse_request(text)
            except HTTPError:
                logging.exception("Exception at Botshot NLU request")

    def _parse_request(self, text):
        payload = {
            "text": text,
            "lang": "en_US",
        }
        resp = requests.get(self.url + '/parse', params=payload)
        resp.raise_for_status()
        return resp.json()


class BotshotExtractor(EntityExtractor):

    def __init__(self):
        super().__init__()
        self.nlu = None

    def extract_entities(self, text: str, max_retries=1):
        if not self.nlu:
            from botshot.nlu.predict import BotshotNLU
            self.nlu = BotshotNLU.load()
            global BOTSHOT_NLU
            BOTSHOT_NLU = self.nlu

        # TODO use a separate thread (pool) to remove TF memory overhead
        return self.nlu.parse(text)


BOTSHOT_NLU = None
