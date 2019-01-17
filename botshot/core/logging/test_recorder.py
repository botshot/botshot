from botshot.core.logging import MessageLogger
from botshot.core.persistence import get_redis
from botshot.core.responses import MessageElement
from botshot.models import ChatMessage
import pickle

DB_KEY = 'test_actions'


class ConversationTestRecorder(MessageLogger):
    ENTITY_KEY = '_admin_test_recording'

    @staticmethod
    def restart():
        get_redis().delete(DB_KEY)

    @staticmethod
    def get_actions():
        raw_actions = get_redis().lrange(DB_KEY, 0, -1)
        return [pickle.loads(raw) for raw in raw_actions]

    def _record(self, type, value):
        action = RecordedAction(type=type, value=value)
        get_redis().rpush(DB_KEY, pickle.dumps(action))

    def log_user_message_start(self, message: ChatMessage, accepted_state):
        self._record(type=RecordedAction.USER_MESSAGE, value=message)

    def log_user_message_end(self, message: ChatMessage, final_state):
        pass

    def log_state_change(self, message: ChatMessage, state):
        self._record(type=RecordedAction.STATE_CHANGE, value=state)

    def log_bot_response(self, message: ChatMessage, response: MessageElement, timestamp):
        self._record(type=RecordedAction.BOT_MESSAGE, value=response)

    def log_error(self, message: ChatMessage, state, exception):
        pass

    @staticmethod
    def get_result_yaml():
        actions = ConversationTestRecorder.get_actions()
        response = ""
        state = None
        return "\n".join([str(action) for action in actions])

        for action in actions[::-1]:
            action = json.loads(action.decode('utf-8'), object_hook=json_deserialize)
            body = action['body']
            print('Action body: {}'.format(body))
            if action['type'] == 'user':
                if body['type'] == 'message':
                    text_entity = body['entities']['_message_text'][0]
                    text = text_entity['value']
                    message = 'UserTextMessage("{}")'.format(text)
                    for entity in body['entities']:
                        if entity.startswith('_'):
                            continue
                        value = body['entities'][entity][0].get('value')
                        if isinstance(value, str):
                            message += '.produces_entity("{}","{}")'.format(entity, value)
                        else:
                            message += '.produces_entity("{}")'.format(entity)
                if body['type'] == 'postback':
                    text_entity = body['entities'].get('_message_text')[0]
                    text = text_entity['value']
                    message = 'UserButtonMessage("{}")'.format(text)
                response += "\n\n" + 'actions.append({})'.format(message) + "\n"
            elif action['type'] == 'bot':
                message = 'BotMessage({})'.format(body['type'])
                if 'text' in body:
                    message += '.with_text("{}")'.format(body['text'])
                response += 'actions.append({})'.format(message)
            elif action['type'] == 'state':
                if body == state:
                    continue
                response += 'actions.append(StateChange("{}"))'.format(body)
                state = body
            response += "\n"

        return response

class RecordedAction:

    USER_MESSAGE = 'user_message'
    BOT_MESSAGE = 'bot_message'
    STATE_CHANGE = 'state_change'

    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __repr__(self):
        return 'RecordedAction({})'.format(self.__dict__)