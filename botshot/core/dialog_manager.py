import logging
from typing import Optional
from django.conf import settings
from botshot.core.chat_session import ChatSession
from botshot.core.flow import FLOWS, Flow, State
from botshot.core.persistence import get_redis, json_serialize, json_deserialize
import logging
import json
from botshot.core.context import Context
from botshot.core.responses.responses import TextMessage
from botshot.core.parsing.user_message import UserMessage
from botshot.core.logging import logging_service
import time


class DialogManager:

    def __init__(self, session: ChatSession):
        self.db = get_redis()
        self.session = session
        self.error_message_text = settings.BOT_CONFIG.get('ERROR_MESSAGE_TEXT')
        if FLOWS is None:
            raise ValueError('Flows not initialized, init_flows() should be called at startup!')
        self.flows = FLOWS
        if self.field_exists('session_state'):
            self.current_state_name = self.get_field('session_state')
            logging.info('Session exists at state {}'.format(self.current_state_name))

            # TODO: is this necessary?
            if self.current_state_name.endswith(':'):
                self.current_state_name = self.current_state_name[:-1] # to avoid infinite loop

            context_dict = self.get_field_json('session_context')
        else:
            self.current_state_name = 'default.root'
            context_dict = {}
            logging.info('Creating new session...')
        self.context = Context.from_dict(dialog=self, data=context_dict)

    def clear(self):
        """Clears all context for this conversation."""
        self.db.hdel('session_state', self.session.chat_id)
        self.db.hdel('session_context', self.session.chat_id)

    def save(self):
        logging.info('Saving state at {}'.format(self.current_state_name))
        self.set_field('session_state', self.current_state_name)
        self.set_field_json('session_context', self.context.to_dict())
        self.set_field('session_interface', self.session.interface.name)

    def get_active_time(self):
        return float(self.get_field('session_active'))

    @staticmethod
    def get_interface_chat_ids():
        return get_redis().hgetall('session_interface')

    def schedule(self, callback_state, at=None, seconds=None):
        """
        Schedules a state transition in the future.
        :param callback_state:  The state to move to.
        :param at:              A datetime with timezone
        :param seconds:         An integer, seconds from now
        """
        from botshot.tasks import accept_schedule_callback
        logging.info('Scheduling callback "{}": at {} / seconds: {}'.format(callback_state, at, seconds))
        if at:
            if at.tzinfo is None or at.tzinfo.utcoffset(at) is None:
                raise Exception('Use datetime with timezone, e.g. "from django.utils import timezone"')
            accept_schedule_callback.apply_async((self, callback_state), eta=at)
        elif seconds:
            accept_schedule_callback.apply_async((self, callback_state), countdown=seconds)
        else:
            raise Exception('Specify either "at" or "seconds" parameter')

    def inactive(self, callback_state, seconds):
        """
        Schedules a state transition in the future, if the user doesn't say anything until then.
        :param callback_state:  The state to move to.
        :param seconds:         An integer, seconds from now
        """
        from botshot.tasks import accept_inactivity_callback
        logging.info('Setting inactivity callback "{}" after {} seconds'.format(callback_state, seconds))
        accept_inactivity_callback.apply_async(
            (self, self.context.counter, callback_state, seconds),
            countdown=seconds)

    def send(self, responses):
        """
        Send one or more messages to the user.
        Shortcut for send_response().
        :param responses:       Instance of MessageElement, str or Iterable.
        """

        if responses is None:
            return

        logging.info('>>> Sending chatbot message')

        if not (isinstance(responses, list) or isinstance(responses, tuple)):
            responses = [responses]

        for response in responses:
            if isinstance(response, str):
                response = TextMessage(text=response)

            # Schedule logging message
            try:
                sent_time = time.time()
                logging_service.log_bot_message.delay(session=self.session, sent_time=sent_time,
                                                      state=self.current_state_name, response=response)
            except Exception as e:
                print('Error scheduling message log', e)

            # Send the response
            self.session.interface.post_message(response)

    def get_field(self, field):
        value = self.db.hget(field, self.session.chat_id)
        return value.decode('utf-8') if value is not None else None

    def set_field(self, field, value):
        return self.db.hset(field, self.session.chat_id, value)

    def set_field_json(self, field, value):
        return self.set_field(field, json.dumps(value, default=json_serialize))

    def get_field_json(self, field):
        value = self.get_field(field)
        return json.loads(value, object_hook=json_deserialize) if value else None

    def field_exists(self, field):
        return self.db.hexists(field, self.session.chat_id)

    def process(self, message: UserMessage):
        self.session.interface.processing_start()
        accepted_state = self.current_state_name
        # Only process messages and postbacks (not 'seen_by's, etc)
        if message.message_type not in ['message', 'postback', 'schedule']:
            return

        logging.info('>>> Received user message')

        # if message_type != 'schedule':
        # TODO don't increment when @ requires -> input and it's valid
        # TODO what to say and do on invalid requires -> input?
        self.context.counter += 1

        self.context.add_message(message)
        self.context.debug()
        # FIXME: Get all current entities from context as EntityValues
        entities = message.payload

        if message.message_type != 'schedule':
            self.set_field('session_active', time.time())

        logging.info('>>> Processing message')

        logging_service.log_user_message.delay(session=self.session, message=message, entities=entities,
                                               state=accepted_state)

        if self._special_message(message.text):
            return
        if self._check_state_transition():
            return
        if self._check_intent_transition(entities):
            return
        if self._check_entity_transition(entities):
            return

        entity_values = self._get_entity_value_tuples(entities)
        if self.get_state().is_supported(entity_values):
            self._run_accept()
            return

        # run 'unsupported' action of the state
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

        self.save()
        self.session.interface.processing_end()

    def _special_message(self, text):
        if not text:
            return False
        if text == '/areyoubotshot':
            # FIXME add Botshot version
            self.send("Botshot Framework")
            return True
        return False

    def _run_accept(self):
        """Runs action of the current state."""
        state = self.get_state()
        if self.current_state_name != 'default.root' and not state.check_requirements(self.context):
            requirement = state.get_first_requirement(self.context)
            self._run_action(requirement.action)
            return
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
        new_state_name = self.context.get_value(entity='_state', max_age=0)
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

    def get_flow(self, flow_name=None) -> Flow:
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

        if '.' not in new_state_name:
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
                    self.send([self.error_message_text])

                # Raise the error if we are in a test
                if self.session.is_test:
                    raise e

        self.save()
        return True


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
            try:
                if include and name not in include:
                    continue
                for value in values:
                    if 'value' in value:
                        entity_set.add((name, value['value']))
            except Exception:
                # someone set this entity to something special
                logging.debug("Skipping entity {} in supported message check".format(name))

        return entity_set
