import json

from django.db import models


class WebMessageData(models.Model):
    uid = models.TextField()
    is_response = models.BooleanField()  # is this a response from the bot?
    timestamp = models.DateTimeField(auto_now=True)
    data = models.TextField()

    data_json = None

    def message(self):
        if not self.data_json:
            self.data_json = json.loads(self.data)
        return self.data_json
