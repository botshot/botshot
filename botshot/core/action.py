import re
from typing import Optional
from django.utils.module_loading import import_string

from botshot.core.responses import TextMessage

from botshot.core.responses import MediaMessage


def create_action(action, relpath: Optional[str] = None):
    """
    Loads action from a definition.
    :param action:      either a string or a function pointer
    :param relpath:     base path for relative imports
    :return:    The loaded action, a function pointer.
    """

    if isinstance(relpath, str):
        relpath = relpath.replace("/", ".")

    if callable(action):
        # action already given as object, everything ok
        return action
    elif isinstance(action, str):
        # dynamically load the function
        try:
            # try to import as absolute path
            return import_string(action)
        except ImportError:
            # try to import relative to flow module
            return import_string(relpath + "." + action)
    elif isinstance(action, dict):
        # load a static action, such as text or image
        return _create_static_action(action)

    raise ValueError("Action class {} not supported".format(type(action)))


def _create_static_action(action_dict: dict):
    """
    Creates an action from a dict definition.
    :param action_dict:
    :return: tuple (action, next_state)
    """
    next = action_dict.get("next")

    if 'type' in action_dict:
        type = action_dict['type'].lower()

        if type == 'image':
            url = action_dict['url']
            return MediaMessage(url=url, media_type='image'), next

        elif type == 'qa':
            if 'context' not in action_dict:
                raise ValueError("QA context not set")
            # TODO
        elif type == 'free_input':
            raise NotImplemented()
        elif type == 'seq2seq':
            raise NotImplemented()
        raise NotImplemented()

    elif 'text' in action_dict:
        message = TextMessage(action_dict['text'])
        if 'replies' in action_dict:
            message.with_replies(action_dict['replies'])
        return message, next

    raise ValueError("Unknown action: {}".format(action_dict))


# TODO: escape $ % , =
def _insert_context_entities(text: str, context):
    new_text, off = "", 0
    for match in re.finditer("%([_A-Za-z0-9]+)/?(!)?", text):
        start, end = match.start(), match.end()
        entity, age_spec = match.group(1), match.group(2)
        entity_filter = context[entity]
        if age_spec == '!':
            entity = entity_filter.value(this_msg=True)
        else:
            entity = entity_filter.value()
        new_text += text[off:start] + entity
        off = end
    new_text += text[off:]
    return new_text


def _insert_strings(text: str, strings):
    new_text, off = "", 0
    for match in re.finditer("\$([._A-Za-z0-9]+)(?:\[(.*)\])?", text):
        start, end = match.start(), match.end()
        string_key, param_spec = match.group(1), match.group(2)
        args = [arg for arg in param_spec.split(",") if '=' not in arg]
        kwargs = dict([arg.split("=", maxsplit=1) for arg in param_spec.split(",") if '=' in arg])
        string_value = strings.get(string_key, *args, **kwargs)
        new_text += text[off:start] + string_value
        off = end
    new_text += text[off:]
    return new_text
