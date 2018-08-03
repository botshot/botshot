from django.urls import path, include
from . import views

urlpatterns = [
    path('botshot/', include('botshot.urls')),
    path('chat/', include('botshot.webgui.urls')),
    path('', views.landing),
]
