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

class ChatLog(models.Model):
    chat_id = models.CharField(max_length=256, primary_key=True)
    first_name = models.CharField(max_length=128, blank=True, null=True)
    last_name = models.CharField(max_length=128, blank=True, null=True)
    image = models.ImageField(upload_to='profile_pic', default='profile_pic/None/no-img.jpg')
    locale = models.CharField(max_length=16, blank=True, null=True)
    last_message_time = models.DateTimeField(blank=True, null=True)

    def save_image(self, image_url, extension=None):
        if not self.chat_id:
            raise ValueError('Save model before saving image, chat_id has to be initialized.')
        tmpfile = save_temporary_image(image_url)
        if not extension:
            path, extension = os.path.splitext(image_url)
        elif not extension.startswith('.'):
            raise ValueError('Image extension has to start with "."')
        self.image.save('{}{}'.format(self.chat_id, extension), tmpfile)

class MessageLog(models.Model):
    message_id = models.BigAutoField(primary_key=True)
    chat = models.ForeignKey(ChatLog, on_delete=models.CASCADE)
    text = models.TextField(blank=True, null=True)
    message_type = models.TextField(max_length=64, blank=True, null=True, db_index=True)
    is_from_user = models.BooleanField()
    time = models.DateTimeField(db_index=True, null=False)
    intent = models.TextField(max_length=256, blank=True, null=True, db_index=True)
    state = models.TextField(max_length=256, blank=True, null=True, db_index=True)
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

# class Attachment(models.Model):  TODO
#     message = models.ForeignKey(Message, on_delete=models.CASCADE)

# class ImageAttachment(Attachment):
#     image_url = models.TextField(max_length=4096, blank=True, null=True)
