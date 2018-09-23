from django.db import models

import requests
import tempfile
import os
from enum import Enum
from jsonfield import JSONField

from botshot.core.persistence import json_serialize, json_deserialize


def save_temporary_image(image_url):
    request = requests.get(image_url, stream=True)

    # Was the request OK?
    if request.status_code != requests.codes.ok:
        return None

    # Create a temporary file
    tmpfile = tempfile.NamedTemporaryFile()

    # Read the streamed image in sections
    for block in request.iter_content(1024 * 8):
        if not block:
            break
        tmpfile.write(block)

    return tmpfile


class ChatConversation(models.Model):
    conversation_id = models.BigAutoField(primary_key=True)
    raw_conversation_id = models.CharField(max_length=256)
    name = models.CharField(max_length=64, blank=True, null=True)
    interface_name = models.CharField(max_length=64, null=False)
    last_message_time = models.DateTimeField(blank=True, null=True)
    state = models.CharField(max_length=128, blank=True, null=True)
    is_test = models.BooleanField(default=False)
    meta = JSONField(null=True, load_kwargs=dict(object_hook=json_deserialize), dump_kwargs=dict(default=json_serialize))
    context_dict = JSONField(null=True, load_kwargs=dict(object_hook=json_deserialize), dump_kwargs=dict(default=json_serialize))

    @property
    def interface(self):
        from botshot.core.interface_factory import InterfaceFactory
        if not self._interface or self._interface.name != self.interface_name:
            self._interface = InterfaceFactory.from_name(self.interface_name)
        return self._interface

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._interface = None


class ChatUser(models.Model):
    user_id = models.BigAutoField(primary_key=True)
    raw_user_id = models.CharField(max_length=256)
    conversation: ChatConversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name='users')
    first_name = models.CharField(max_length=64, blank=True, null=True)
    last_name = models.CharField(max_length=64, blank=True, null=True)
    image = models.ImageField(upload_to='profile_pic', default='images/icon_user.png')
    locale = models.CharField(max_length=16, blank=True, null=True)
    last_message_time = models.DateTimeField(blank=True, null=True)

    def save_image(self, image_url, extension=None):
        if not self.user_id:
            raise ValueError('Save model before saving image, user_id has to be initialized.')
        tmpfile = save_temporary_image(image_url)
        if not extension:
            path, extension = os.path.splitext(image_url)
        elif not extension.startswith('.'):
            raise ValueError('Image extension has to start with "."')
        self.image.save('{}{}'.format(self.user_id, extension), tmpfile)


class ChatMessage(models.Model):
    MESSAGE = 'message'
    BUTTON = 'button'
    SCHEDULE = 'schedule'
    EVENT = 'event'

    message_id = models.BigAutoField(primary_key=True)
    user: ChatUser = models.ForeignKey(ChatUser, on_delete=models.CASCADE, related_name='messages')
    type = models.TextField(max_length=16, choices=[(v, v) for v in [MESSAGE, BUTTON, SCHEDULE, EVENT]], null=False)
    text = models.TextField(blank=True, null=True)
    is_user = models.BooleanField()
    time = models.DateTimeField(db_index=True, null=False)
    intent = models.TextField(max_length=64, blank=True, null=True, db_index=True)
    state = models.TextField(max_length=128, blank=True, null=True, db_index=True)
    entities = JSONField(null=True, load_kwargs=dict(object_hook=json_deserialize), dump_kwargs=dict(default=json_serialize))
    response_dict = JSONField(null=True, load_kwargs=dict(object_hook=json_deserialize), dump_kwargs=dict(default=json_serialize))