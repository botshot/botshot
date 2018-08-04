import json
import logging
import os
import time
from typing import Optional

from django.conf import settings

from botshot.core.chat_session import ChatSession
from botshot.core.responses.responses import TextMessage
from botshot.tasks import accept_inactivity_callback, accept_schedule_callback
from .context import Context
from .flow import load_flows_from_definitions, State
from .logger import MessageLogging
from .persistence import get_redis
from .serialize import json_deserialize, json_serialize
from .tests import ConversationTestRecorder


class DialogManager:
    version = '1.34'

    def __init__(self, session: ChatSession):
        self.session = session
        self.uid = session.chat_id  # for backwards compatibility
        self.logger = MessageLogging(self)
        self.db = get_redis()
        self.context = None  # type: Context

        self.should_log_messages = settings.BOT_CONFIG.get('SHOULD_LOG_MESSAGES', False)
        self.error_message_text = settings.BOT_CONFIG.get('ERROR_MESSAGE_TEXT')

        context_dict = {}
        version = self.db.get('dialog_version')
        logging.info('Initializing dialog for chat %s...' % session.chat_id)
        self.current_state_name = None
        self._init_flows()

        if self.get_state("default.root") is None:
            raise Exception("Required state default.root was not found. "
                            "Please add this state, Botshot uses it as the first state when starting a conversation.")

        if version and version.decode('utf-8') == DialogManager.version and \
                self.db.hexists('session_context', self.session.chat_id):

            state = self.db.hget('session_state', self.session.chat_id).decode('utf-8')
            logging.info('Session exists at state %s' % state)

            if not state:
                logging.error("State was NULL, sending user to default.root!")
                state = 'default.root'
            elif state.endswith(':'):
                state = state[:-1]  # to avoid infinite loop

            self._move_to(state, initializing=True)
            context_string = self.db.hget('session_context', self.session.chat_id)
            context_dict = json.loads(context_string.decode('utf-8'), object_hook=json_deserialize)
        else:
            self.current_state_name = 'default.root'
            logging.info('Creating new session...')
            self.logger.log_user(self.session)

        self.context = Context.from_dict(dialog=self, data=context_dict)  # type: Context

    def _init_flows(self):
        flow_definitions = self._create_flows()
        self.flows = load_flows_from_definitions(flow_definitions)
        self.current_state_name = 'default.root'

    def _create_flows(self):
        """Creates flows from their YAML definitions."""
        import yaml
        flows = {}  # a dict with all the flows loaded from YAML
        BOTS = settings.BOT_CONFIG.get('BOTS', [])
        for filename in BOTS:
            try:
                with open(os.path.join(settings.BASE_DIR, filename)) as f:
                    file_flows = yaml.load(f)
                    if not file_flows:
                        logging.warning("Skipping empty flow definition {}".format(filename))
                        break
                    for flow in file_flows:
                        if flow in flows:
                            raise Exception("Error: duplicate flow {}".format(flow))
                        flows[flow] = file_flows[flow]
                        flows[flow]['relpath'] = os.path.dirname(filename)  # directory of relative imports
            except OSError as e:
                raise ValueError("Unable to open definition {}".format(filename)) from e
            except TypeError as e:
                raise ValueError("Unable to read definition {}".format(filename)) from e
        return flows

    @staticmethod
    def clear_chat(chat_id):
        """Clears all context for this conversation."""
        db = get_redis()
        db.hdel('session_state', chat_id)
        db.hdel('session_context', chat_id)

    def process(self, message_type, entities):
        self.session.interface.processing_start(self.session)
        accepted_time = time.time()
        accepted_state = self.current_state_name
        # Only process messages and postbacks (not 'seen_by's, etc)
        if message_type not in ['message', 'postback', 'schedule']:
            return

        logging.info('>>> Received user message')

        # if message_type != 'schedule':
        # TODO don't increment when @ requires -> input and it's valid
        # TODO what to say and do on invalid requires -> input?
        self.context.counter += 1

        entities = self.context.add_entities(entities)
        # remove keys with empty values
        entities = {k: v for k, v in entities.items() if v is not None}

        if self.test_record_message(message_type, entities):
            return
        elif self._special_message(message_type, entities):
            return

        if message_type != 'schedule':
            self.save_inactivity_callback()

        logging.info('>>> Processing message')

        if not self._check_state_transition() \
            and not self._check_intent_transition(entities) \
            and not self._check_entity_transition(entities):

                entity_values = self._get_entity_value_tuples(entities)
                if self.get_state().is_supported(entity_values):
                    self._run_accept(save_identical=True)
                    self.save_state()
                else:
                    # run 'unsupported' action of the state
                    entities['_unsupported'] = [{"value": True}]

                    if self.get_state().unsupported:
                        self._run_action(self.get_state().unsupported)
                    # if not provided, run 'unsupported' action of the flow
                    elif self.get_flow().unsupported:
                        self._run_action(self.get_flow().unsupported)
                    # if not provided, give up and go to default.root
                    else:
                        raise Exception("Missing required 'unsupported' action field in flow {}.".format(
                            self.get_flow().name)
                        )
                    self.save_state()

        self.session.interface.processing_end(self.session)

        # leave logging message to the end so that the user does not wait
        self.logger.log_user_message(message_type, entities, accepted_time, accepted_state)

    def schedule(self, callback_name, at=None, seconds=None):
        logging.info('Scheduling callback "{}": at {} / seconds: {}'.format(callback_name, at, seconds))
        if at:
            if at.tzinfo is None or at.tzinfo.utcoffset(at) is None:
                raise Exception('Use datetime with timezone, e.g. "from django.utils import timezone"')
            accept_schedule_callback.apply_async((self.session.to_json(), callback_name), eta=at)
        elif seconds:
            accept_schedule_callback.apply_async((self.session.to_json(), callback_name), countdown=seconds)
        else:
            raise Exception('Specify either "at" or "seconds" parameter')

    def inactive(self, callback_name, seconds):
        logging.info('Setting inactivity callback "{}" after {} seconds'.format(callback_name, seconds))
        accept_inactivity_callback.apply_async(
            (self.session.to_json(), self.context.counter, callback_name, seconds),
            countdown=seconds)

    def save_inactivity_callback(self):
        self.db.hset('session_active', self.session.chat_id, time.time())
        callbacks = settings.BOT_CONFIG.get('INACTIVE_CALLBACKS')
        if not callbacks:
            return
        for name in callbacks:
            seconds = callbacks[name]
            self.inactive(name, seconds)

    def test_record_message(self, message_type, entities):
        record, record_age = self.context.get_age('test_record')
        self.recording = False
        if not record:
            return False
        if record_age == 0:
            if record.value == 'start':
                self.send_response(ConversationTestRecorder.record_start())
            elif record.value == 'stop':
                self.send_response(ConversationTestRecorder.record_stop())
            else:
                self.send_response("Use /test_record/start/ or /test_record/stop/")
            self.save_state()
            return True
        if record == 'start':
            ConversationTestRecorder.record_user_message(message_type, entities)
            self.recording = True
        return False

    def _special_message(self, type, entities):
        text = entities.get("_message_text", [])
        text = text[0] if len(text) else None
        text = text.get("value") if text else None

        if not isinstance(text, str):
            return False
        elif text == '/areyoubotshot':
            self.send_response("Botshot Framework Dialog Manager v{}".format(self.version))
            return True
        elif text.startswith('/intent/'):
            intent = text.replace('/intent/', '', count=1)
            self.context.set_value("intent", intent)
            return True
        return False

    def _run_accept(self, save_identical=False):
        """Runs action of the current state."""
        state = self.get_state()
        if self.current_state_name != 'default.root' and not state.check_requirements(self.context):
            requirement = state.get_first_requirement(self.context)
            self._run_action(requirement.action)
        else:
            if not state.action:
                logging.warning('State {} does not have an action.'.format(self.current_state_name))
                return
            self._run_action(state.action)

    def _run_action(self, fn):
        if not callable(fn):
            logging.error("Error: Trying to run a function of type {}".format(type(fn)))
            return
        # run the action
        retval = fn(dialog=self)
        # send a response if given in return value
        if retval and not isinstance(retval, str):
            raise ValueError("Error: Action must return either None or a state name.")
        self._move_to(retval)

    def _check_state_transition(self):
        """Checks if entity _state was received in current message (and moves to the state)"""
        new_state_name = self.context._state.get_value(this_msg=True)
        if new_state_name is not None:
            return self._move_to(new_state_name)
        return False

    def _check_intent_transition(self, entities: dict):
        """Checks if intent was parsed from current message (and moves by intent)"""
        intent = self.context.intent.get_value(this_msg=True)
        if not intent:
            return False

        entity_values = self._get_entity_value_tuples(entities, include=("intent", "_message_text"))
        if self.get_state().is_supported(entity_values):
            return False

        # move to the flow whose 'intent' field matches intent

        # Check accepted intent of the current flow's states
        flow = self.get_flow()
        new_state_name = flow.get_state_for_intent(intent)

        # Check accepted intent of all flows
        if not new_state_name:
            for flow in self.flows.values():
                if flow.matches_intent(intent):
                    new_state_name = flow.name + '.root'
                    break

        if not new_state_name:
            logging.error('Error! Found intent "%s" but no flow present for it!' % intent)
            return False

        logging.info('Moving based on intent %s...' % intent)
        return self._move_to(new_state_name + ":")  # : runs the action

    def _check_entity_transition(self, entities: dict):
        """ Checks if entity was parsed from current message (and moves if associated state exists)"""
        # FIXME somehow it also uses older entities

        # first check if supported, if yes, abort
        entity_values = self._get_entity_value_tuples(entities)
        if self.get_state().is_supported(entity_values):
            return False

        # TODO check states of current flow for 'accepted' first

        new_state_name = None

        # then check if there is a flow that would accept the entity
        for flow in self.flows.values():
            if flow.accepts_message(entities.keys()):
                new_state_name = flow.name + '.root'  # TODO might use a state that accepts it instead?
                break

        if new_state_name:
            logging.info("Moving by entity")
            return self._move_to(new_state_name + ":")

        return False

    def get_flow(self, flow_name=None):
        """Returns a Flow object by its name. Defaults to current flow."""
        if not flow_name:
            flow_name, _ = self.current_state_name.split('.', 1)
        return self.flows.get(flow_name)

    def get_state(self, flow_state_name=None) -> Optional[State]:
        """Returns a State object by its name. Defaults to current state."""
        flow_name, state_name = (flow_state_name or self.current_state_name).split('.', 1)
        flow = self.get_flow(flow_name)
        return flow.get_state(state_name) if flow else None

    def _move_to(self, new_state_name, initializing=False, save_identical=False):
        """Moves to a state by its full name."""
        logging.info("Trying to move to {}".format(new_state_name))

        # if flow prefix is not present, add the current one
        if isinstance(new_state_name, int):
            new_state = self.context.get_history_state(new_state_name - 1)
            new_state_name = new_state['name'] if new_state else None
        if not new_state_name:
            new_state_name = self.current_state_name

        if new_state_name.count(':'):
            new_state_name, action = new_state_name.split(':', 1)
            action = True
        else:
            action = False

        if ('.' not in new_state_name):
            new_state_name = self.current_state_name.split('.')[0] + '.' + new_state_name
        if not self.get_state(new_state_name):
            logging.warning('Error: State %s does not exist! Staying at %s.' % (new_state_name, self.current_state_name))
            return False
        identical = new_state_name == self.current_state_name
        if not initializing and (not identical or save_identical):
            self.context.add_state(new_state_name)
        if not new_state_name:
            return False
        previous_state = self.current_state_name
        self.current_state_name = new_state_name
        if not initializing:

            # notify the interface that the state was changed
            self.session.interface.state_change(self.current_state_name)
            # record change if recording tests
            if self.recording:
                ConversationTestRecorder.record_state_change(self.current_state_name)

            try:
                if previous_state != new_state_name and action:
                    logging.info("Moving from {} to {} and executing action".format(
                        previous_state, new_state_name
                    ))
                    self._run_accept()
                elif action:
                    logging.info("Staying in state {} and executing action".format(previous_state))
                    self._run_accept()
                elif previous_state != new_state_name:
                    logging.info("Moving from {} to {} and doing nothing".format(previous_state, new_state_name))
                else:
                    logging.info("Staying in state {} and doing nothing".format(previous_state))

            except Exception as e:

                context_debug = "(can't load context)"
                try:
                    context_debug = self.context.debug()
                except:
                    pass

                logging.exception(
                              '*****************************************************\n'
                              'Exception occurred while running action {} of state {}\n'
                              'Chat id: {}\n'
                              'Context: {}\n'
                              '*****************************************************'
                              .format(action, new_state_name, self.session.chat_id, context_debug)
                )

                if self.error_message_text:
                    self.send_response([self.error_message_text])

                # Raise the error if we are in a test
                if self.session.is_test:
                    raise e

        self.save_state()
        return True

    def save_state(self):
        if not self.context:
            return
        logging.info('Saving state at %s' % (self.current_state_name))
        self.db.hset('session_state', self.session.chat_id, self.current_state_name)
        context_json = json.dumps(self.context.to_dict(), default=json_serialize)
        self.db.hset('session_context', self.session.chat_id, context_json)
        self.db.hset('session_interface', self.session.chat_id, self.session.interface.name)
        self.db.set('dialog_version', DialogManager.version)

        # save chat session to redis, TODO
        session = json.dumps(self.session.to_json())
        self.db.hset("chat_session", self.session.chat_id, session)

    def send_response(self, responses):
        """
        Send one or more messages to the user.
        :param responses:       Instance of MessageElement, str or Iterable.
        """

        if responses is None:
            return

        logging.info('>>> Sending chatbot message')

        if not (isinstance(responses, list) or isinstance(responses, tuple)):
            return self.send_response([responses])

        for response in responses:
            if isinstance(response, str):
                response = TextMessage(text=response)

            # Send the response
            self.session.interface.post_message(self.session, response)

            # Record if recording
            if self.recording:
                ConversationTestRecorder.record_bot_message(response)

        for response in responses:
            # Log the response
            self.logger.log_bot_message(response, self.current_state_name)

    def send(self, responses):
        """
        Send one or more messages to the user.
        Shortcut for send_response().
        :param responses:       Instance of MessageElement, str or Iterable.
        """
        return self.send_response(responses)

    def _get_entity_value_tuples(self, entities: dict, include=tuple()):
        """
        Builds a set of [entity names + tuples (entity_name, entity_value)].
        Used for checking whether the current state supports the received message.
        """
        entity_set = set()
        # add entity names
        entity_set = entity_set.union(entities.keys())

        # add tuples (name, value)
        for name, values in entities.items():
            if include and name not in include:
                continue
            for value in values:
                if 'value' in value:
                    entity_set.add((name, value['value']))

        return entity_set
