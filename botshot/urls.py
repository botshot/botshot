from django.conf import settings
from django.conf.urls import url, include
from rest_framework import routers

from botshot.models import MessageLog
from . import views

secret_url = settings.BOT_CONFIG.get('WEBHOOK_SECRET_URL')
urlpatterns = [
    url(r'^messenger/{}/?$'.format(secret_url),
        view=views.FacebookView.as_view(), name='messenger'),
    url(r'^telegram/{}/?$'.format(secret_url),
        view=views.TelegramView.as_view(), name='telegram'),
    url(r'^gactions/{}/?$'.format(secret_url),
        view=views.GActionsView.as_view(), name='gactions'),
    url(r'^skype/{}/?$'.format(secret_url),
        view=views.SkypeView.as_view(), name='skype'),

    url(r'^log/?$', views.log),
    url(r'^log/chats/?$', views.ChatLogViewSet.as_view({'get': 'list'})),
    url(r'^log/messages/(?P<chat_id>[a-zA-Z_0-9]+)/?$', views.MessageLogList.as_view())

    #url(r'^log/?$', views.log),
    #url(r'^log/users/?$', views.log_users),
    #url(r'^log/messages/(?P<user_id>[a-zA-Z_0-9]+)/?$', views.log_messages)
]
