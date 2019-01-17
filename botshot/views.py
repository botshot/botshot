import json
import logging
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse, JsonResponse
from django.template import loader
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, renderers, generics, pagination

from botshot.core.interface_factory import InterfaceFactory
from botshot.core.logging.test_recorder import ConversationTestRecorder
from botshot.core.persistence import get_redis
from botshot.core.tests import _run_test_module
from botshot.models import ChatMessage, ChatConversation, ChatUser
from botshot.serializers import ChatConversationSerializer, ChatMessageSerializer, ChatUserSerializer

@csrf_exempt
def interface_webhook(request, interface_name):
    # print(request.body.decode('utf8'))
    interface = InterfaceFactory.from_name(interface_name)
    return interface.webhook(request)


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


@login_required(login_url=reverse_lazy('login'))
def run_test(request, name):
    benchmark = request.GET.get('benchmark', False)
    return JsonResponse(data=_run_test_module(name, benchmark=benchmark))


@login_required(login_url=reverse_lazy('login'))
def test_recording(request):
    recorded_yaml = ConversationTestRecorder.get_result_yaml()
    context = {
        'recorded_yaml': recorded_yaml
    }
    template = loader.get_template('botshot/test_recording.html')
    return HttpResponse(template.render(context, request))


@login_required(login_url=reverse_lazy('login'))
def log(request):
    context = {}
    template = loader.get_template('botshot/log.html')
    return HttpResponse(template.render(context,request))


class StandardResultsSetPagination(pagination.PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000


class ChatConversationViewSet(viewsets.ModelViewSet):
    queryset = ChatConversation.objects.order_by('-last_message_time')
    serializer_class = ChatConversationSerializer
    renderer_classes = [renderers.JSONRenderer]
    pagination_class = StandardResultsSetPagination

class ChatUserViewSet(viewsets.ModelViewSet):
    queryset = ChatUser.objects.all()
    serializer_class = ChatUserSerializer
    renderer_classes = [renderers.JSONRenderer]
    pagination_class = StandardResultsSetPagination

class ChatMessageList(generics.ListAPIView):
    serializer_class = ChatMessageSerializer
    renderer_classes = [renderers.JSONRenderer]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = ChatMessage.objects.order_by('-time','-pk')
        conversation_id = self.kwargs.get('conversation_id')
        if conversation_id:
            queryset = queryset.filter(user__conversation_id=conversation_id)
        return queryset
