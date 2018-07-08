from django.conf import settings
from django.conf.urls import url

from botshot.core import strings
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
    url(r'^run_all_tests/?$', views.run_all_tests),
    url(r'^run_test/(?P<name>[a-zA-Z0-9_\-]+)/?$', views.run_test),
    url(r'^run_test_message/(?P<message>[a-zA-Z0-9 _\-]+)/?$', views.run_test_message),
    url(r'^log/(?P<user_limit>[0-9]*)/?$', views.log),
    url(r'^log_tests/?$', views.log_tests),
    url(r'^test/?$', views.test),
    url(r'^debug/?$', views.debug),
    url(r'^test_record/?$', views.test_record),
    url(r'^users/?', views.users_view),
    url(r'^log_conversation/(?P<group_id>[a-zA-Z_0-9]*)/(?P<page>[0-9]*)/?$', views.log_conversation),
    url(r'^strings/?$', strings.string_view, name='string_list'),
    url(r'^strings/edit/(?P<key>.+)?$', strings.detail_view, name='string_detail'),
    url(r'^strings/update', strings.update_view, name="string_update"),
]
