from django.conf import settings
from django.conf.urls import url
from django.contrib.auth import views as auth_views

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

    url(r'^$', views.index, name='dashboard'),
    url(r'^login/$', auth_views.LoginView.as_view(template_name='botshot/login/login.html'), name='login'),

    url(r'^flows/?$', views.flows, name='flows'),

    url(r'^test/?$', views.test, name='test'),
    url(r'^test/run/(?P<name>[a-zA-Z0-9_\-]+)/?$', views.run_test, name='run_test'),

    url(r'^log/?$', views.log, name='log'),
    url(r'^log/chats/?$', views.ChatLogViewSet.as_view({'get': 'list'}), name="log/chats"),
    url(r'^log/messages/(?P<chat_id>[a-zA-Z_0-9]*)/?$', views.MessageLogList.as_view(), name="log/messages"),
    # url(r'^log/tests/?$', views.log_tests), TODO log tests and users
    # url(r'^log/users/?$', views.log_users),
]
