import pytest
from mock import Mock

from botshot.core.persistence import json_serialize, json_deserialize


class TestSerialize:

    def test_serialize_deserialize_message(self):
        from botshot.core.responses import TextMessage
        from botshot.core.responses import LinkButton
        obj = TextMessage(text="foo", buttons=[LinkButton(title="foo", url="http://example.com", webview=True)])
        obj.__hidden__ = 'bar'
        data = json_serialize(obj)
        assert data and data['__type__'] == obj.__class__.__module__ + "." + obj.__class__.__name__
        assert data['text'] == 'foo' and data['buttons'][0]['title'] == 'foo'
        obj = json_deserialize(data)
        assert obj and isinstance(obj, TextMessage)
        assert obj.buttons[0] and isinstance(obj.buttons[0], LinkButton)
        assert obj.text == "foo" and obj.buttons[0].url == "http://example.com"
        assert not hasattr(obj, '__hidden__')

    def test_serialize_invalid(self):
        obj = Mock()
        assert json_serialize(obj) == obj

    def test_deserialize_invalid(self):
        obj = {"__type__": 123}
        assert json_deserialize(obj) is None
        obj = {"__type__": "i.dont.exist"}
        assert json_deserialize(obj) is None
