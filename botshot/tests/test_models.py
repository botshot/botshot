import pytest
from botshot.core.responses import TextMessage, MessageElement
from botshot.models import ChatMessage


@pytest.mark.django_db
class TestModels:

    def test_response_serialization(self):
        response = TextMessage(text="Hello, world!")
        model = ChatMessage()
        model.response_dict = response
        assert isinstance(model.response, MessageElement)
        assert isinstance(model.serialized_response, dict)
        assert model.serialized_response['__type__'] == response.__module__ + "." + response.__class__.__name__
