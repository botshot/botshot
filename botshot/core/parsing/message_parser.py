import logging
import emoji
import re
import time
from django.conf import settings
from botshot.core.parsing.entity_extractor import EntityExtractor
from django.utils.module_loading import import_string

ENTITY_EXTRACTORS = []

def register_extractor(extractor):
    """Registers an entity extractor class."""
    if isinstance(extractor, str):
        cls = import_string(extractor)
        logging.debug("Registering entity extractor %s", cls)
        ENTITY_EXTRACTORS.append(cls())
    elif issubclass(extractor, EntityExtractor):
        logging.debug("Registering entity extractor %s", extractor)
        ENTITY_EXTRACTORS.append(extractor())
    elif isinstance(extractor, EntityExtractor):
        raise ValueError("Error: Please register entity extractor class instead of instance.")
    else:
        raise ValueError("Error: Entity extractor must be a subclass of botshot.core.parsing.entity_extractor.EntityExtractor")


for classname in settings.BOT_CONFIG.get("ENTITY_EXTRACTORS", []):
    register_extractor(classname)


def add_default_extractors():
    # compatibility for old chatbots
    if "WIT_TOKEN" in settings.BOT_CONFIG and "ENTITY_EXTRACTORS" not in settings.BOT_CONFIG:
        logging.warning("Adding wit extractor from wit token")
        from botshot.core.parsing import wit_extractor
        ENTITY_EXTRACTORS.append(wit_extractor.WitExtractor())


add_default_extractors()


def parse_text_entities(text, num_tries=1):
    entities = {}

    if len(ENTITY_EXTRACTORS) <= 0:
        logging.warning('No entity extractors configured!')
    else:
        for extractor in ENTITY_EXTRACTORS:
            append = extractor.extract_entities(text)
            for entity, values in append.items():
                entities.setdefault(entity, []).extend(values)

    append = parse_special_text_entities(text)

    for (entity, value) in re.findall(re.compile(r'/([^/]+)/([^/]+)/'), text):
        if not entity in append:
            append[entity] = []
        append[entity].append({'value': value})

    # add all new entity values
    for entity, values in append.items():
        if not entity in entities:
            entities[entity] = []
        entities[entity] += values

    return entities


def parse_special_text_entities(text):
    # TODO custom nlp might receive them preprocessed (or not)
    entities = {}
    chars = {':)': ':slightly_smiling_face:', '(y)': ':thumbs_up_sign:', ':(': ':disappointed_face:',
             ':*': ':kissing_face:', ':O': ':face_with_open_mouth:', ':D': ':grinning_face:',
             '<3': ':heavy_black_heart:️', ':P': ':face_with_stuck-out_tongue:'}
    demojized = emoji.demojize(text)
    char_emojis = re.compile(
        r'(' + '|'.join(chars.keys()).replace('(', '\(').replace(')', '\)').replace('*', '\*') + r')')
    demojized = char_emojis.sub(lambda x: chars[x.group()], demojized)
    if demojized != text:
        match = re.compile(r':([a-zA-Z_0-9]+):')
        for emoji_name in re.findall(match, demojized):
            if 'emoji' not in entities:
                entities['emoji'] = []
            entities['emoji'].append({'value': emoji_name})
        # if re.match(match, demojized):
        #    entities['intent'].append({'value':'emoji'})
    return entities
