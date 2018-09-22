import json
import logging
from datetime import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse, JsonResponse
from django.template import loader
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, renderers, generics, pagination

from botshot.core.interfaces.facebook import FacebookInterface
from botshot.core.interfaces.microsoft import MicrosoftInterface
from botshot.core.interfaces.telegram import TelegramInterface
from botshot.core.persistence import get_redis
from botshot.core.tests import _run_test_module
from botshot.models import ChatLog, MessageLog
from botshot.serializers import ChatLogSerializer, MessageLogSerializer



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


@login_required(login_url=reverse_lazy('login'))
def index(request):
    context = {}
    template = loader.get_template('botshot/index.html')
    return HttpResponse(template.render(context,request))


@login_required(login_url=reverse_lazy('login'))
def flows(request):
    from botshot.core.flow import FLOWS
    context = {
        'flows': FLOWS
    }
    template = loader.get_template('botshot/flows.html')
    return HttpResponse(template.render(context,request))


# TODO this really needs improvement
@login_required(login_url=reverse_lazy('login'))
def test(request):
    # TODO use SQL database
    db = get_redis()
    results = db.hgetall('test_results')
    results = [json.loads(results[k].decode('utf-8')) for k in sorted(list(results))] if results else []

    updated_time = db.get('test_time')
    updated_time = db.get('test_time').decode('utf-8') if updated_time else None
    updated_time = datetime.strptime(updated_time, "%Y-%m-%d %H:%M:%S.%f") if updated_time else None
    # updated_time = naturaltime(updated_time) if updated_time else None

    status = 'passed'
    avg = {'duration': 0, 'total': 0, 'init': 0, 'parsing': 0, 'processing': 0}
    passed = 0
    for test in results:
        result = test['result']
        if result['status'] == 'passed':
            passed += 1
            avg['duration'] += result['duration']
            avg['total'] += result['report']['avg']['total']
            avg['init'] += result['report']['avg']['init']
            avg['parsing'] += result['report']['avg']['parsing']
            avg['processing'] += result['report']['avg']['processing']
        elif status != 'exception':
            status = result['status']

    if passed > 0:
        for key in avg:
            avg[key] = avg[key] / passed

    context = {'tests': results, 'avg': avg, 'status': status, 'updated_time': updated_time}
    template = loader.get_template('botshot/test.html')
    return HttpResponse(template.render(context, request))


def run_test(request, name):
    benchmark = request.GET.get('benchmark', False)
    return JsonResponse(data=_run_test_module(name, benchmark=benchmark))


@login_required(login_url=reverse_lazy('login'))
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
