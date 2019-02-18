from botshot.core.interfaces import BotshotInterface
from botshot.models import ChatUser


class TestInterface(BotshotInterface):

    name = 'test'
    messages = []
    states = []

    def webhook(self, request):
        pass

    def send_responses(self, user: ChatUser, responses):
        pass

    def broadcast_responses(self, users, responses):
        pass

    @staticmethod
    def clear():
        TestInterface.messages = []
        TestInterface.states = []

    @staticmethod
    def fill_session_profile(session):
        if not session:
            raise ValueError("Session is None")
        session.profile = Profile(first_name='Test', last_name='')
        return session

    @staticmethod
    def post_message(session, response):
        TestInterface.messages.append(response)

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
        if not TestInterface.states or TestInterface.states[-1] != state:
            TestInterface.states.append(state)

    @staticmethod
    def parse_message(user_message, num_tries=1):
        return user_message
