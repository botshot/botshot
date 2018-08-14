from django.db import models
from botshot.core.serialize import json_serialize, json_deserialize
import json

class ChatLog(models.Model):
    chat_id = models.CharField(max_length=256, primary_key=True)
    first_name = models.CharField(max_length=128, blank=True, null=True)
    last_name = models.CharField(max_length=128, blank=True, null=True)
    image_url = models.CharField(max_length=256, blank=True, null=True)
    locale = models.CharField(max_length=16, blank=True, null=True)

    last_message_time = models.DateTimeField(blank=True, null=True)


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
        return json.loads(self.meta_raw, object_hook=json_deserialize)

    @property
    def response_dict(self):
        if self.is_from_user:
            return None
        return json.loads(self.meta_raw, object_hook=json_deserialize)

    def set_entities(self, entities):
        self.meta_raw = json.dumps(entities, default=json_serialize)

    def set_response_dict(self, response_dict):
        self.meta_raw = json.dumps(response_dict, default=json_serialize)

# class Attachment(models.Model):  TODO
#     message = models.ForeignKey(Message, on_delete=models.CASCADE)

# class ImageAttachment(Attachment):
#     image_url = models.TextField(max_length=4096, blank=True, null=True)
