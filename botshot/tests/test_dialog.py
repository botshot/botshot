import pytest
import mock

from botshot.core.chat_manager import ChatManager
from botshot.core.dialog import Dialog
from botshot.core.responses import TextMessage


class TestDialog:

    def test_send_messages(self):
        message, context, logger = mock.Mock(), mock.Mock(), mock.Mock()
        chat_mgr = ChatManager()
        dialog = Dialog(message, context, chat_mgr, logger)

        chat_mgr.send = mock.Mock()        
        dialog.send("Hello world")
        assert chat_mgr.send.called
        
        chat_mgr.send = mock.Mock()
        dialog.send(TextMessage("Hi"))
        assert chat_mgr.send.called

        with pytest.raises(ValueError):
            dialog.send(105)
        
        with pytest.raises(ValueError):
            dialog.send([None, None])
