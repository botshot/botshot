import logging
import os
import tempfile

import pytz
import requests

from botshot.core.persistence import json_serialize, json_deserialize
from django.db import models
from jsonfield import JSONField


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
    raw_conversation_id = models.CharField(max_length=255, db_index=True)
    name = models.CharField(max_length=64, blank=True, null=True)
    interface_name = models.CharField(max_length=64, null=False)
    last_message_time = models.DateTimeField(blank=True, null=True)
    state = models.CharField(max_length=128, blank=True, null=True)
    is_test = models.BooleanField(default=False)
    meta = JSONField(null=True, load_kwargs=dict(object_hook=json_deserialize), dump_kwargs=dict(default=json_serialize))
    context_dict = JSONField(null=True, load_kwargs=dict(object_hook=json_deserialize), dump_kwargs=dict(default=json_serialize))

    @property
    def id(self):
        return self.conversation_id

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
    raw_user_id = models.CharField(max_length=255, db_index=True)
    conversations = models.ManyToManyField(ChatConversation, related_name="users")
    first_name = models.CharField(max_length=64, blank=True, null=True)
    last_name = models.CharField(max_length=64, blank=True, null=True)
    image = models.ImageField(upload_to='profile_pic', default='images/icon_user.png')
    locale = models.CharField(max_length=16, blank=True, null=True)
    last_message_time = models.DateTimeField(blank=True, null=True)
    profile = JSONField(blank=True, null=True)  # arbitrary profile, managed by chat interface

    def save_image(self, image_url, extension=None):
        if not image_url:
            logging.warning("Profile image is None in save_image, ignoring")
            return
        if not self.user_id:
            raise ValueError('Save user before saving profile image, user_id has to be initialized.')
        if not extension:
            path, extension = os.path.splitext(image_url)
        if extension.startswith('.'):
            extension = extension[1:]

        # FIXME: secure MEDIA_ROOT directory or clients will see all pics!
        tmpfile = save_temporary_image(image_url)
        self.image.save('%s.%s' % (self.user_id, extension), tmpfile)


class ChatMessage(models.Model):
    MESSAGE = 'message'
    BUTTON = 'button'
    SCHEDULE = 'schedule'
    EVENT = 'event'

    message_id = models.BigAutoField(primary_key=True)
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name="messages")
    user = models.ForeignKey(ChatUser, on_delete=models.CASCADE, null=True, related_name='messages')
    type = models.TextField(max_length=16, choices=[(v, v) for v in [MESSAGE, BUTTON, SCHEDULE, EVENT]], null=False)
    text = models.TextField(blank=True, null=True)
    is_user = models.BooleanField()
    time = models.DateTimeField(db_index=True, null=False)
    state = models.TextField(max_length=128, blank=True, null=True)
    entities = JSONField(null=True, load_kwargs=dict(object_hook=json_deserialize), dump_kwargs=dict(default=json_serialize))
    response_dict = JSONField(null=True, load_kwargs=dict(object_hook=json_deserialize), dump_kwargs=dict(default=json_serialize))
    supported = models.BooleanField(default=True)

    @property
    def response(self):
        """This method is guaranteed to return the response as a MessageElement subclass."""
        if self.response_dict:
            return self.response_dict
        return None

    @property
    def serialized_response(self):
        """This method is guaranteed to return the response as a JSON dict."""
        if self.response_dict:
            return json_serialize(self.response_dict)
        return None

    def __repr__(self):
        return 'ChatMessage({})'.format({k:v for k, v in self.__dict__.items() if k not in ['_state']})


class ScheduledAction(models.Model):

    _id = models.BigAutoField(primary_key=True)
    description = models.TextField(null=True, blank=True)
    _at = models.DateTimeField(null=False, blank=False, db_index=True)
    recurrence = JSONField(null=True, load_kwargs=dict(object_hook=json_deserialize), dump_kwargs=dict(default=json_serialize))
    _until = models.DateTimeField(null=True)
    action = JSONField(load_kwargs=dict(object_hook=json_deserialize), dump_kwargs=dict(default=json_serialize))
    conversations = JSONField(load_kwargs=dict(object_hook=json_deserialize), dump_kwargs=dict(default=json_serialize))
    is_done = models.BooleanField(default=False, db_index=True)

    @property
    def at(self):
        return self._at.replace(tzinfo=pytz.UTC)

    @property
    def until(self):
        if self._until:
            return self._until.replace(tzinfo=pytz.UTC)
        return None
