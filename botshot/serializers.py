from botshot.models import ChatLog, MessageLog
from rest_framework import serializers

class ChatLogSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ChatLog
        fields = ('chat_id', 'first_name', 'last_name', 'image_url', 'locale', 'last_message_time')

class MessageLogSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MessageLog
        fields = ('message_id', 'message_type', 'text', 'is_from_user', 'time', 'intent', 'state', 'entities', 'response_dict')
