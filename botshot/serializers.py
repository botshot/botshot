from botshot.models import ChatConversation, ChatUser, ChatMessage
from rest_framework import serializers

class ChatConversationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ChatConversation
        fields = ()#('chat_id', 'first_name', 'last_name', 'image', 'locale', 'last_message_time')

class ChatUserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ChatUser
        fields = ()#('message_id', 'message_type', 'text', 'is_from_user', 'time', 'intent', 'state', 'entities', 'response_dict')

class ChatMessageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ()#('message_id', 'message_type', 'text', 'is_from_user', 'time', 'intent', 'state', 'entities', 'response_dict')
