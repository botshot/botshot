from django.test import TestCase

from botshot.core.interfaces.adapter.telegram import TelegramAdapter
from botshot.core.responses.buttons import LinkButton, PayloadButton
from botshot.core.responses.quick_reply import QuickReply
from botshot.core.responses.responses import TextMessage, GenericTemplateMessage, GenericTemplateElement
from botshot.core.responses.templates import ListTemplate


class TelegramAdapterTest(TestCase):
    def test_chat_id(self):
        adapter = TelegramAdapter(1099511627776)
        self.failUnless(adapter.id == 1099511627776)
        adapter = TelegramAdapter('1099511627776')
        self.failUnless(adapter.id == 1099511627776)
        try:
            adapter = TelegramAdapter('foo')
            self.fail()
        except:
            pass

    def test_text_message(self):
        chat_id = '0'
        adapter = TelegramAdapter(chat_id)
        message = TextMessage(text='Hello world!')
        print(adapter.to_response(message))

    def test_text_message_with_replies(self):
        chat_id = '0'
        adapter = TelegramAdapter(chat_id)
        message = TextMessage(text='Hello world!')
        message.add_quick_reply(QuickReply(title='A'))
        message.add_quick_reply(QuickReply(title='B'))
        print(adapter.to_response(message))

    def test_text_message_with_buttons(self):
        chat_id = '0'
        adapter = TelegramAdapter(chat_id)
        message = TextMessage(text='Hello world!')
        message.add_button(LinkButton(title='A', url='http://example.com'))
        message.add_button(
            PayloadButton(title='B', payload={'_state': 'default.root:accept', 'item_id': 'e_12345_67890'}))
        print(adapter.to_response(message))

    def test_generic_template_message(self):
        chat_id = '0'
        adapter = TelegramAdapter(chat_id)
        message = GenericTemplateMessage()
        for i in range(3):
            url = 'http://placehold.it/300x200'
            element = GenericTemplateElement(title='foo', subtitle='lorem ipsum dolor sit amet.', image_url=url)
            message.add_element(element)
        response = adapter.to_response(message)
        print(response)

    def test_list_template_message(self):
        chat_id = '0'
        adapter = TelegramAdapter(chat_id)
        message = ListTemplate()
        for i in range(3):
            url = 'http://placehold.it/300x200'
            element = GenericTemplateElement(title='foo', subtitle='lorem ipsum dolor sit amet.', image_url=url)
            message.add_element(element)
        response = adapter.to_response(message)
        print(response)

    def test_unknown_message(self):
        chat_id = '0'
        adapter = TelegramAdapter(chat_id)
        print(adapter.to_response('<?php alert("WASSUP"); ?>'))
