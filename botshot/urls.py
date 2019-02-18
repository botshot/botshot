from django.conf import settings
from django.conf.urls import url
from django.contrib.auth import views as auth_views

from . import views

secret_url = settings.BOT_CONFIG.get('WEBHOOK_SECRET_URL')
urlpatterns = [
    url(r'^webhook/(?P<interface_name>[a-zA-Z_0-9]*)/{}/?$'.format(secret_url), view=views.interface_webhook, name='interface_webhook'),

    url(r'^$', views.index, name='dashboard'),
    url(r'^login/$', auth_views.LoginView.as_view(template_name='botshot/login/login.html'), name='login'),

    url(r'^flows/?$', views.flows, name='flows'),

    url(r'^test/recording/?$', views.test_recording, name='botshot-test-recording'),
    url(r'^test/?$', views.test, name='test'),
    url(r'^test/run/(?P<name>[a-zA-Z0-9_\-]+)/?$', views.run_test, name='run_test'),

    url(r'^log/?$', views.log, name='log'),
    url(r'^log/conversations/?$', views.ChatConversationViewSet.as_view({'get': 'list'}), name="log/conversations"),
    url(r'^log/users/?$', views.ChatUserViewSet.as_view({'get': 'list'}), name="log/users"),
    url(r'^log/messages/(?P<chat_id>[a-zA-Z_0-9]*)/?$', views.ChatMessageList.as_view(), name="log/messages"),
    # url(r'^log/tests/?$', views.log_tests), TODO log tests and users
    # url(r'^log/users/?$', views.log_users),
]
