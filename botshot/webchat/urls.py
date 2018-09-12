from django.conf.urls import url

from .views import *

urlpatterns = [
    # url(r'(?P<uid>[0-9]+)', view=webchat, name='webchat'),
    url(r'^$', view=webchat, name='webchat'),
    url(r'^login/?$', view=do_login, name='do_login'),
    url(r'^logout/?$', view=do_logout, name='do_logout'),
    url(r'^last_change/$', view=get_last_change, name='last_change')
]
