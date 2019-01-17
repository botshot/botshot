from abc import abstractmethod, ABC
from django.urls import reverse
from botshot.core.dialog import Dialog
from botshot.core.logging.test_recorder import ConversationTestRecorder
from botshot.core.responses import TextMessage, PayloadButton, LinkButton


class DialogInterceptor(ABC):

    @abstractmethod
    def intercept(self, dialog: Dialog) -> bool:
        return False


class BotshotVersionDialogInterceptor(DialogInterceptor):

    def intercept(self, dialog: Dialog) -> bool:
        if dialog.message.text == '/areyoubotshot':
            from botshot import __version__
            dialog.send("Botshot Framework version {}".format(__version__))
            return True
        return False


class AdminDialogInterceptor(DialogInterceptor):

    def intercept(self, dialog: Dialog) -> bool:
        if dialog.message.text == '/admin':
            #if not dialog.message.user.is_admin:
            #    dialog.send('You are not admin.')
            #    return False
            response = TextMessage('Admin actions')
            if dialog.context.get(ConversationTestRecorder.ENTITY_KEY):
                response.add_button(PayloadButton('Stop recording', payload={ConversationTestRecorder.ENTITY_KEY: False}))
            else:
                response.add_button(PayloadButton('Start recording', payload={ConversationTestRecorder.ENTITY_KEY: True}))
            dialog.send(response)
            return True
        test_recording = dialog.context.get_value(ConversationTestRecorder.ENTITY_KEY, max_age=0)
        if test_recording:
            response = TextMessage('Test conversation recording started.')
            response.add_button(PayloadButton('Stop recording', payload={ConversationTestRecorder.ENTITY_KEY: False}))
            dialog.send(response)
            ConversationTestRecorder.restart()
            return True
        elif test_recording == False:
            response = TextMessage('Test conversation recording done. View Botshot Recording tab.')
            response.add_button(PayloadButton('Start again', payload={ConversationTestRecorder.ENTITY_KEY: True}))
            dialog.send(response)
            return True
        return False
