from django.db import models


class User(models.Model):
    uid = models.CharField(max_length=255, primary_key=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    surname = models.CharField(max_length=255, blank=True, null=True)
    message_cnt = models.PositiveIntegerField(default=0)

    def get_chats(self):
        chats = Chat.objects.filter(user_uid=self)
        return chats


class Chat(models.Model):
    chat_id = models.CharField(max_length=255, primary_key=True)
    user_uid = models.ForeignKey(User, on_delete=models.CASCADE)


class Message(models.Model):
    id = models.BigAutoField(primary_key=True)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    text = models.TextField(blank=True, null=True)
    is_from_user = models.BooleanField()
    time = models.DateTimeField(auto_now=True)
    intent = models.TextField(max_length=255, blank=True, null=True, db_index=True)
    state = models.TextField(max_length=255, blank=True, null=True, db_index=True)


class QuickReply(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    text = models.TextField(max_length=255, blank=False, null=False)
    # TODO was_clicked : boolean

# class Attachment(models.Model):  TODO
#     message = models.ForeignKey(Message, on_delete=models.CASCADE)

# class ImageAttachment(Attachment):
#     image_url = models.TextField(max_length=4096, blank=True, null=True)
