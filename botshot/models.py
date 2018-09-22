from django.db import models
from botshot.core.persistence import todict
import json
import requests
import tempfile
import os

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

class ChatSession(models.Model):
    session_id = models.CharField(max_length=256, primary_key=True)
    name = models.CharField(max_length=64, blank=True, null=True)
    last_message_time = models.DateTimeField(blank=True, null=True)

class ChatUser(models.Model):
    user_id = models.CharField(max_length=256, primary_key=True)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='users')
    first_name = models.CharField(max_length=64, blank=True, null=True)
    last_name = models.CharField(max_length=64, blank=True, null=True)
    image = models.ImageField(upload_to='profile_pic', default='profile_pic/None/no-img.jpg')
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
    message_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(ChatUser, on_delete=models.CASCADE, related_name='messages')
    text = models.TextField(blank=True, null=True)
    message_type = models.TextField(max_length=32, blank=True, null=True, db_index=True)
    is_from_user = models.BooleanField()
    time = models.DateTimeField(db_index=True, null=False)
    intent = models.TextField(max_length=64, blank=True, null=True, db_index=True)
    state = models.TextField(max_length=128, blank=True, null=True, db_index=True)
    meta_raw = models.TextField(blank=True, null=True, db_index=False)

    @property
    def entities(self):
        if not self.is_from_user:
            return None
        return json.loads(self.meta_raw)

    @property
    def response_dict(self):
        if self.is_from_user:
            return None
        return json.loads(self.meta_raw)

    def set_entities(self, entities):
        self.meta_raw = json.dumps(entities)

    def set_response(self, response):
        response_dict = todict(response)
        self.meta_raw = json.dumps(response_dict)