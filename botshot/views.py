import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse, JsonResponse
from django.template import loader
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers

from botshot.core.interfaces.facebook import FacebookInterface
from botshot.core.interfaces.microsoft import MicrosoftInterface
from botshot.core.interfaces.telegram import TelegramInterface
from botshot.core.logging.elastic import get_elastic
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from botshot.models import ChatLog, MessageLog
from botshot.serializers import ChatLogSerializer, MessageLogSerializer
from rest_framework import viewsets, renderers, generics, pagination


class FacebookView(generic.View):

    def get(self, request, *args, **kwargs):
        if self.request.GET.get('hub.verify_token') == settings.BOT_CONFIG.get('WEBHOOK_VERIFY_TOKEN'):
            return HttpResponse(self.request.GET['hub.challenge'])
        else:
            return HttpResponse('Error, invalid token')

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)

    # Post function to handle Facebook messages
    def post(self, request, *args, **kwargs):
        # Converts the text payload into a python dictionary
        request_body = json.loads(self.request.body.decode('utf-8'))
        FacebookInterface.accept_request(request_body)
        return HttpResponse()


class TelegramView(generic.View):

    def get(self, request, *args, **kwargs):
        request_body = json.loads(self.request.body.decode('utf-8'))
        from pprint import pprint
        pprint(request_body)
        return HttpResponse()

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)

    # Post function to handle Telegram messages
    def post(self, request, *args, **kwargs):
        # Converts the text payload into a python dictionary
        request_body = json.loads(self.request.body.decode('utf-8'))
        TelegramInterface.accept_request(request_body)
        return HttpResponse()


class GActionsView(generic.View):
    def get(self, request, *args, **kwargs):
        return HttpResponse()

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        from botshot.core.interfaces.google import GoogleActionsInterface
        body = json.loads(self.request.body.decode('utf-8'))
        logging.info(body)
        resp = GoogleActionsInterface.accept_request(body)
        return JsonResponse(resp)


class SkypeView(generic.View):
    def get(self, request, *args, **kwargs):
        body = json.loads(self.request.body.decode('utf-8'))
        MicrosoftInterface.accept_request(body)
        return HttpResponse()

    def post(self, request, *args, **kwargs):
        body = json.loads(self.request.body.decode('utf-8'))
        MicrosoftInterface.accept_request(body)
        return HttpResponse()

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)


#@login_required
def log(request):
    context = {}
    template = loader.get_template('botshot/log.html')
    return HttpResponse(template.render(context,request))

class StandardResultsSetPagination(pagination.PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000

class ChatLogViewSet(viewsets.ModelViewSet):
    queryset = ChatLog.objects.order_by('-last_message_time')
    serializer_class = ChatLogSerializer
    renderer_classes = [renderers.JSONRenderer]
    pagination_class = StandardResultsSetPagination

class MessageLogList(generics.ListAPIView):
    serializer_class = MessageLogSerializer
    renderer_classes = [renderers.JSONRenderer]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = MessageLog.objects.order_by('-time','-pk')
        chat_id = self.kwargs.get('chat_id')
        if chat_id:
            queryset = queryset.filter(chat_id=chat_id)
        return queryset
