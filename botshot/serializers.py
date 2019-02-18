from botshot.models import ChatConversation, ChatUser, ChatMessage
from rest_framework import serializers

class JSONSerializerField(serializers.Field):
    def to_internal_value(self, data):
        return data
    def to_representation(self, value):
        return value


class ChatUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatUser
        fields = ('user_id', 'first_name', 'last_name', 'locale', 'image')


class ChatConversationSerializer(serializers.ModelSerializer):
    users = ChatUserSerializer(many=True, read_only=True)

    class Meta:
        model = ChatConversation
        fields = ('conversation_id', 'name', 'interface_name', 'last_message_time', 'users')


class ChatMessageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChatMessage
        fields = ('message_id', 'text', 'type', 'is_user', 'time', 'entities', 'response_dict')
