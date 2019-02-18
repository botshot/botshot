from botshot.core.chat_session import ChatSession, Profile
from botshot.core.parsing.message_parser import parse_text_message
from botshot.core.persistence import get_redis
from botshot.core.responses import TextMessage
from botshot.tasks import accept_user_message


class GoogleActionsInterface():
    name = 'google_actions'
    prefix = 'goog'
    messages = []
    states = []

    response_cache = {}

    @staticmethod
    def clear():
        GoogleActionsInterface.messages = []
        GoogleActionsInterface.states = []

    @staticmethod
    def fill_session_profile(session: ChatSession):
        if not session:
            raise ValueError("Session is None")
        session.profile = Profile(first_name='Test', last_name='')
        return session

    @staticmethod
    def post_message(session, response):
        GoogleActionsInterface.messages.append(response)
        get_redis().set("response_for_{id}".format(id=session.chat_id), str(response))  # TODO

    @staticmethod
    def convert_responses(session, responses):

        # TODO
        response = responses or "Hello world!"

        if isinstance(response, TextMessage):
            text = response.text
        elif isinstance(response, str):
            text = response
        else:
            text = "Dummy response"

        json_response = {
            "conversationToken": session.meta.get("chat_id"),
            "expectUserResponse": True,
            "expectedInputs": [
                {
                    "inputPrompt": {
                        "richInitialPrompt": {
                            "items": [
                                {
                                    "simpleResponse": {
                                        "textToSpeech": text,
                                        # "Howdy! I can tell you fun facts about almost any number, like 42. What do you have in mind?",
                                        "displayText": text
                                        # "Howdy! I can tell you fun facts about almost any number. What do you have in mind?"
                                    }
                                }
                            ],
                            "suggestions": []
                        }
                    },
                    "possibleIntents": [
                        {
                            "intent": "actions.intent.TEXT"
                        }
                    ]
                }
            ]
        }

        return json_response
        # return json.dumps(json_response)

    @staticmethod
    def send_settings(settings):
        pass

    @staticmethod
    def processing_start(session):
        pass

    @staticmethod
    def processing_end(session):
        pass

    @staticmethod
    def state_change(state):
        if not GoogleActionsInterface.states or GoogleActionsInterface.states[-1] != state:
            GoogleActionsInterface.states.append(state)

    @staticmethod
    def accept_request(body):
        uid = body['user']['userId']
        chat_id = body['conversation']['conversationId']
        meta = {"uid": uid, "chat_id": chat_id}
        profile = Profile(uid, None, None)
        session = ChatSession(GoogleActionsInterface, chat_id, meta, profile)
        accept_user_message.delay(session, body).get()
        # responses = GoogleActionsInterface.response_cache.get(session.chat_id)
        responses = get_redis().get("response_for_{id}".format(id=session.chat_id))  # TODO
        return GoogleActionsInterface.convert_responses(session, responses.decode('utf8'))

    @staticmethod
    def parse_message(msg, num_tries=1):
        # intent = msg['inputs']['intent']
        # if intent == "assistant.intent.action.MAIN":
        #     intent = 'default'
        text = msg['inputs'][0]['rawInputs'][0]['query']
        parsed = parse_text_message(text)
        return parsed
