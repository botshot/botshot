import json
import logging
import pickle

from django.conf import settings
from wit import Wit
from wit.wit import WitError

from botshot.core.parsing import date_utils, EntityExtractor
from botshot.core.persistence import get_redis


class WitExtractor(EntityExtractor):

    def __init__(self):
        super().__init__()
        self.log = logging.getLogger()
        self.wit_token = settings.BOT_CONFIG.get('WIT_TOKEN')
        if not self.wit_token:
            raise ValueError("Wit token not set! Please set it as settings.BOT_CONFIG['WIT_TOKEN'].")
        self.cache_key = 'wit_cache'
        self.cache = settings.BOT_CONFIG.get('WIT_ENABLE_CACHE', True)
        # self.clear_wit_cache()

    def extract_entities(self, text: str, max_retries=5, **kwargs):
        if max_retries <= 0:
            self.log.error("Maximal number of Wit retries reached")
            return {}
        cached = self._load_from_cache(text)
        if cached: return cached
        try:
            wit_client = Wit(access_token=self.wit_token, actions={})
            entities = wit_client.message(text).get('entities', {})
            entities = self._process_wit_entities(entities)
            self.save_to_cache(text, entities)
            return entities
        except WitError:
            self.log.exception('Wit error:')
            return self.extract_entities(text, max_retries - 1)

    def _process_wit_entities(self, entities: dict):

        entities = self._process_metadata(entities)

        if 'datetime' in entities:
            datetime = entities['datetime']
            duration = entities.get('duration', None)
            append = date_utils.process_datetime(datetime, duration)
            entities.update(append)

        return entities

    def _process_metadata(self, entities: dict):
        for entity, values in entities.items():
            for value in values:
                # parse string metadata from Wit into a dict
                metadata = value.get('metadata')
                if metadata and isinstance(metadata, str):
                    try:
                        value['metadata'] = json.loads(metadata)
                    except:
                        self.log.warning("Ignoring invalid metadata for entity {}: {}".format(
                            entity, metadata
                        ))
                        value['metadata'] = None
        return entities

    def _load_from_cache(self, text):
        if self.cache:
            db = get_redis()
            if db.hexists('wit_cache', text):
                parsed = pickle.loads(db.hget('wit_cache', text))
                self.log.debug('Got cached wit key: "{}" = {}'.format(self.cache_key, parsed))
                return parsed
        return None

    def save_to_cache(self, text, entities):
        if self.cache and 'date_interval' not in entities:
            db = get_redis()
            self.log.debug('Caching wit key: {} = {}'.format(text, entities))
            db.hset('wit_cache', text, pickle.dumps(entities))

    def clear_wit_cache(self):
        if self.cache:
            self.log.debug('Clearing Wit cache...')
            db = get_redis()
            db.delete('wit_cache')


def teach_wit(wit_token, entity, values, doc=""):
    import requests
    logging.warning('*** TEACHING WIT ***')
    params = {'v':'20160526'}
    logging.warning('Inserting values of {}'.format(entity))
    rsp = requests.request(
        'PUT',
        'https://api.wit.ai/entities/'+entity,
        headers={
            'authorization': 'Bearer ' + wit_token,
            'accept': 'application/json'
        },
        params=params,
        json={'doc':doc or entity, 'values':values}
    )
    if rsp.status_code > 200:
        raise ValueError('Wit responded with status: ' + str(rsp.status_code) +
                       ' (' + rsp.reason + '): ' + rsp.text)
    json = rsp.json()
    if 'error' in json:
        raise ValueError('Wit responded with an error: ' + json['error'])
