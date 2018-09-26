import logging
from botshot.core.logging.abs_logger import MessageLogger


class ConversationTestRecorder(MessageLogger):

    def log_user_message(self, message, accepted_state, final_state):
        pass

    def log_state_change(self, message, state):
        pass

    def log_bot_response(self, message, response, timestamp):
        pass

    def log_error(self, message, state, exception):
        pass

    @staticmethod
    def record_user_message(message_type, entities):
        logging.warning('Recording user {}: {}'.format(message_type, message))
        db = get_redis()
        db.lpush('test_actions', json.dumps({'type': 'user', 'body': {'type': message_type, 'entities': message}},
                                            default=json_serialize))

    @staticmethod
    def record_bot_message(message):
        record = {'type': type(message).__name__}
        if isinstance(message, TextMessage):
            record['text'] = message.text
        logging.warning('Recording bot message: {}'.format(record))
        db = get_redis()
        db.lpush('test_actions', json.dumps({'type': 'bot', 'body': record}))

    @staticmethod
    def record_state_change(state):
        logging.warning('Recording state change: {}'.format(state))
        db = get_redis()
        db.lpush('test_actions', json.dumps({'type': 'state', 'body': state}))

    @staticmethod
    def record_start():
        logging.warning('Starting recording')
        db = get_redis()
        db.delete('test_actions')
        message = TextMessage(text="Starting to record ;)") \
            .add_button(PayloadButton(title="Stop recording", payload={"test_record": "stop"}))
        return message

    @staticmethod
    def record_stop():
        logging.warning('Stopping recording')
        deploy_url = settings.BOT_CONFIG.get('DEPLOY_URL', "localhost:8000")
        message = TextMessage("Done recording ;)") \
            .add_button(LinkButton(title='Get result', url=deploy_url + '/botshot/test_record')) \
            .add_button(PayloadButton(title='Start again', payload={"test_record": "start"}))
        return [message]

    @staticmethod
    def get_result():
        db = get_redis()
        actions = db.lrange('test_actions', 0, -1)
        response = """from botshot.core.responses import *
from botshot.core.tests import *

actions = []
"""
        state = None
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
