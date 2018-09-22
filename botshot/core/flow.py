from typing import Optional
import importlib
import re
from abc import abstractmethod, ABC
from django.conf import settings
from botshot.core.responses import AttachmentMessage
import os
import logging
from inspect import getsource

FLOWS = None


def init_flows():
    """Creates flows from their YAML definitions."""
    global FLOWS
    import yaml
    flows = {}  # a dict with all the flows loaded from YAML
    BOTS = settings.BOT_CONFIG.get('BOTS', [])
    for filename in BOTS:
        try:
            with open(os.path.join(settings.BASE_DIR, filename)) as f:
                definitions = yaml.load(f)
                if not definitions:
                    logging.warning("Skipping empty flow definition {}".format(filename))
                    break
                for flow_name in definitions:
                    if flow_name in flows:
                        raise Exception("Error: duplicate flow {}".format(flow_name))
                    definition = definitions[flow_name]
                    flow = Flow.load(flow_name, definition, relpath=os.path.dirname(filename))
                    flows[flow_name] = flow
        except OSError as e:
            raise ValueError("Unable to open definition {}".format(filename)) from e
        except TypeError as e:
            raise ValueError("Unable to read definition {}".format(filename)) from e

    if not flows.get('default') or not flows.get('default').get_state('root'):
        raise Exception("Required state default.root was not found. "
                        "Please add this state, Botshot uses it as the first state when starting a conversation.")

    print('Initialized {} flows: {}'.format(len(flows), sorted(list(flows.keys()))))

    FLOWS = flows


class State:
    def __init__(self, name: str, action, intent=None, requires=None, is_temporary=False, supported=None,
                 unsupported=None):
        """
        Construct a conversation state.
        :param name:            name of this state
        :param action:          function that will run when moving to this state
        :param intent
        :param requires
        :param is_temporary     whether the action should fire just once,
                                 after that, the state will be used just as a basis for transitions
                                 and unrecognized messages will move to default.root instead.
        :param supported        set of entities that will not trigger a state change (- state can handle them)
                                 for specific values, use tuples like this: (entity_name, entity_value)
        :param unsupported      an optional function to handle unsupported messages
        """
        self.name = str(name)
        self.action = action
        self.intent = intent
        self.requires = requires
        self.is_temporary = is_temporary
        self.supported = supported or set()
        self.unsupported = unsupported

    @staticmethod
    def load(definition: dict, relpath: Optional[str]) -> tuple:
        """
        Loads state from a dictionary definition.
        :param definition:      a dict containing the state definition (e.g. from YAML)
        :param relpath:         base path for relative action imports
        :return: tuple (state_name, state)
        """
        name = definition['name']
        action = None
        if 'action' in definition:
            action = definition['action']
            action = State.make_action(action, relpath)
        requires = State.parse_requirements(definition.get('require'), relpath)
        intent = definition.get("intent")
        is_temporary = definition.get("temporary", False)

        supported = set()
        for obj in definition.get("supports", []):
            if isinstance(obj, dict):
                # it is a list of supported values along with entity name
                for entity_name, value in obj.items():  # dict of (name: value)
                    if isinstance(value, str):
                        supported.add((entity_name, value))
                    else:
                        # finally, it can be a list of supported values for this entity
                        for v in value:
                            supported.add((entity_name, v))

            elif isinstance(obj, str):
                # it is a simple entity name - string
                supported.add(obj)
            else:
                raise ValueError("Unknown data type in supported entity list: {}".format(type(obj)))

        # TODO add local entities
        supported = supported.union([r.entity for r in requires if isinstance(r, EntityRequirement)])

        if 'unsupported' in definition:
            unsupported = State.make_action(definition.get("unsupported"), relpath)
        else:
            unsupported = None

        s = State(
            name=name,
            action=action,
            intent=intent,
            requires=requires,
            is_temporary=is_temporary,
            supported=supported,
            unsupported=unsupported
        )
        return name, s

    @staticmethod
    def make_action(action, relpath: Optional[str] = None):
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
                rel_module, fn_name = action.rsplit(".", maxsplit=1)
                try:
                    # try to import as relative path
                    module = importlib.import_module(rel_module)
                except:
                    # try to import as absolute path
                    abs_module = relpath + "." + rel_module
                    module = importlib.import_module(abs_module)

                fn = getattr(module, fn_name)
                return fn
            except Exception as e:
                raise Exception("An error occurred while importing action {}. See the exception above.".format(action)) from e
        elif isinstance(action, dict):
            # load a static action, such as text or image
            return State.make_default_action(action)

        raise ValueError("Action class {} not supported".format(type(action)))

    @staticmethod
    def make_default_action(action_dict):
        """
        Creates an action from a non-function definition.
        :param action_dict:
        :return: The created action, a function pointer.
        """
        from botshot.core.responses import TextMessage
        next = action_dict.get("next")
        message = None
        if 'type' in action_dict:
            type = action_dict['type'].lower()
            if type == 'qa':
                if 'context' not in action_dict:
                    raise ValueError("QA context not set")
                # TODO
            elif type == 'free_input': pass
            elif type == 'seq2seq': pass
            message = TextMessage("TO DO")
        elif 'text' in action_dict:
            message = TextMessage(action_dict['text'])
            if 'replies' in action_dict:
                message.with_replies(action_dict['replies'])
        elif 'image_url' in action_dict:
            message = AttachmentMessage('image', action_dict['image_url'])

        if not message:
            raise ValueError("Unknown action: {}".format(action_dict))
        return dynamic_response_fn(message, next)

    @staticmethod
    def parse_requirements(reqs_raw, relpath: Optional[str]):
        reqs = []
        if reqs_raw is None:
            return reqs

        for req in reqs_raw:
            req_cond = req.get("condition")
            entity = req.get("entity")

            if req_cond and entity:
                raise ValueError("Error: either use a requirement entity or a condition, not both")
            elif req_cond:
                req_cond = State.make_action(req_cond, relpath)
                action = State.make_action(req.get("action"), relpath)
                reqs.append(ConditionRequirement(
                    condition=req_cond,
                    action=action
                ))
            elif entity:
                reqs.append(EntityRequirement(
                    slot=req.get("slot"),
                    entity=req.get("entity"),
                    filter=req.get("filter"),
                    action=State.make_action(req.get("action"), relpath)
                ))

        return reqs

    def set_requires(self, **kwargs):
        """Add required entities to this state. Useful to check for e.g. user's location."""
        self.requires.append(EntityRequirement(**kwargs))
        return self

    def check_requirements(self, context) -> bool:
        """Checks whether the requirements of this state are met."""
        for requirement in self.requires:
            if not requirement.matches(context):
                return False
        return True

    def get_first_requirement(self, context):
        """Returns the first requirement of this state."""
        for requirement in self.requires:
            if not requirement.matches(context):
                return requirement
        return True

    def get_action_code(self):
        return getsource(self.action) if callable(self.action) else None

    def is_supported(self, msg_entities: set) -> bool:
        """Checks whether this state can handle a message with given entities."""
        return not self.supported.isdisjoint(msg_entities)

    def __str__(self):
        return "state:" + self.name


class Flow:
    def __init__(self, name: str, states=None, intent=None, unsupported=None):
        """
        Construct a new flow instance.
        :param name:   name of this flow
        :param states: dict of states (optional)
        :param intent: accepted intents regex (optional)
        :param unsupported      a function to handle unsupported messages
        """

        # if unsupported is None:
        #     raise ValueError("Missing required 'unsupported' action field in flow {}.".format(name))

        self.name = str(name)
        self.states = states or {}
        self.intent = intent or self.name
        self.accepted = set()
        self.unsupported = unsupported

    @staticmethod
    def load(name, data: dict, relpath: str):
        states = dict(State.load(s, relpath) for s in data["states"])
        intent = data.get("intent", name)
        unsupported = None
        if 'unsupported' in data:
            unsupported = State.make_action(data['unsupported'], relpath)
        flow = Flow(name=name, states=states, intent=intent, unsupported=unsupported)
        flow.accepted = set(data.get('accepts', {}))
        return flow

    def __getitem__(self, state_name: str):
        return self.states[state_name]

    def get_state(self, state_name: str):
        return self.states.get(state_name)

    def add_state(self, state: State):
        """Adds a state to this flow."""
        if isinstance(state, State):
            self.states[state.name] = state
            return self
        raise ValueError("Argument must be an instance of State")

    def get_state_for_intent(self, intent) -> str or None:
        """Returns name of the first state that receives an intent."""
        for name, state in self.states.items():
            if state.intent and re.match(state.intent, intent):
                return self.name + "." + name
        return None

    def matches_intent(self, intent) -> bool:
        """Checks whether this flow accepts an intent."""
        return re.match(self.intent, intent) is not None

    def set_accepts(self, entity_name):
        """Add accepted entity."""
        self.accepted.add(entity_name)
        return self

    def accepts_message(self, entities: list) -> bool:
        """
        Checks whether this flow accepts a message with given entities.
        Used for entity transitions.
        """
        return not self.accepted.isdisjoint(entities)

    def __str__(self):
        return "flow:" + self.name


class Requirement(ABC):
    @abstractmethod
    def matches(self, context) -> bool:
        pass


class EntityRequirement(Requirement):
    def __init__(self, slot, entity, filter=None, message=None, action=None):
        self.slot = slot
        self.entity = entity
        self.filter = filter
        self.action = action or dynamic_response_fn(message)
        if not self.action:
            raise ValueError("Requirement has no message nor action")

    def matches(self, context) -> bool:
        if self.entity not in context:
            return False
        if self.filter is not None:
            from botshot.core.entity_query import EntityQuery
            # TODO move to new class PreparedFilter
            eq = EntityQuery.from_yaml(context, self.entity, self.filter)
            return eq.count() > 0
        return True


class ConditionRequirement(Requirement):
    def __init__(self, condition, message=None, action=None):
        self.condition = condition
        self.action = action or dynamic_response_fn(message)
        if not self.condition:
            raise ValueError("Requirement has no condition set")
        if not self.action:
            raise ValueError("Requirement has no message nor action")

    def matches(self, context) -> bool:
        return self.condition(context)


def dynamic_response_fn(messages, next=None):
    def fn(dialog):
        dialog.send(messages)
        return next
    return fn
