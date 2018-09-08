import datetime
import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import loader
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

from botshot.core.interfaces import init_webhooks
from botshot.core.interfaces.facebook import FacebookInterface
from botshot.core.interfaces.microsoft import MicrosoftInterface
from botshot.core.interfaces.telegram import TelegramInterface
from botshot.core.logging.elastic import get_elastic
from botshot.core.persistence import get_redis
from botshot.core.tests import ConversationTestRecorder, UserTextMessage, _get_test_modules, _run_test_module, \
    _run_test_actions

print("Initializing webhooks ...")
init_webhooks()


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


@login_required(login_url=reverse_lazy('login'))
def run_all_tests(request):
    modules = _get_test_modules()

    print('Running tests: {}'.format(modules))
    tests = []
    db = get_redis()
    db.delete('test_results')
    for module in modules:
        print('Running tests "{}"'.format(module))
        tests.append(_run_test_module(module))

    db.set('test_time', str(datetime.datetime.now()))

    return JsonResponse(data=tests, safe=False)


# TODO this really needs improvement
@login_required(login_url=reverse_lazy('login'))
def test(request):
    db = get_redis()
    results = db.hgetall('test_results')
    results = [json.loads(results[k].decode('utf-8')) for k in sorted(list(results))] if results else []

    updated_time = db.get('test_time')
    updated_time = db.get('test_time').decode('utf-8') if updated_time else None

    status = 'passed'
    avg = {'duration':0, 'total':0, 'init':0, 'parsing':0, 'processing':0}
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

    context = {'tests':results, 'avg':avg, 'status':status, 'updated_time' : updated_time}
    template = loader.get_template('botshot/test.html')
    return HttpResponse(template.render(context, request))

def run_test(request, name):
    benchmark = request.GET.get('benchmark', False)
    return JsonResponse(data=_run_test_module(name, benchmark=benchmark))

def run_test_message(request, message):
    return _run_test_actions('message', [UserTextMessage(message)])


def test_record(request):
    response = ConversationTestRecorder.get_result()

    response = HttpResponse(content_type='application/force-download', content=response) #
    response['Content-Disposition'] = 'attachment; filename=mytest.py'
    return response


@login_required(login_url=reverse_lazy('login'))
def log_tests(request):

    es = get_elastic()
    if not es:
        return HttpResponse('not able to connect to elasticsearch')

    res = es.search(index="message-log", doc_type='message', body={
    "size": 0,
    "aggs" : {
        "test_ids" : {
            "terms" : { "field" : "test_id",  "size" : 500 }
        }
    }})
    test_ids = []
    for bucket in res['aggregations']['test_ids']['buckets']:
        test_id = bucket['key']
        test_name = test_id.replace('_',' ').capitalize()
        test_ids.append({'id':'test_id_'+test_id, 'name':test_name})


    context = {
        'groups' : test_ids
    }
    template = loader.get_template('botshot/log.html')
    return HttpResponse(template.render(context,request))


@login_required(login_url=reverse_lazy('login'))
def log(request, user_limit):

    user_limit = int(user_limit) if user_limit else 100
    es = get_elastic()
    if not es:
        return HttpResponse('not able to connect to elasticsearch')

    res = es.search(index="message-log", doc_type='message', body={
       "size": 0,
       "aggs": {
          "uids": {
             "terms": {
                "field": "uid",
                "size": 1000
             },
             "aggs": {
                "created": {
                   "max": {
                      "field": "created"
                   }
                }
             }
          }
       }
    })
    uids = []
    for bucket in res['aggregations']['uids']['buckets']:
        uid = bucket['key']
        last_time = bucket['created']['value']
        uids.append({'uid':uid, 'last_time':last_time})

    uids = sorted(uids, key=lambda uid: -uid['last_time'])[:user_limit]


    res = es.search(index="message-log", doc_type='user', body={
       "size" : user_limit,
       "query": {
            "bool" : {
                "filter" : {
                    "terms" : { "uid" : [u['uid'] for u in uids] }
                }
            }
        }
    })

    user_map = {user['_source']['uid']: {'name' : '{} {}'.format(user['_source']['profile'].get('first_name'), user['_source']['profile'].get('last_name')), 'id' : 'uid_{}'.format(user['_source']['uid'])} for user in res['hits']['hits'] if user['_source']}
    users = [user_map[u['uid']] if u['uid'] in user_map else {'id':'uid_'+u['uid'], 'name':u['uid']} for u in uids]

    context = {
        'groups': users
    }

    print(users)
    template = loader.get_template('botshot/log.html')
    return HttpResponse(template.render(context,request))

def log_conversation(request, group_id=None, page=1):
    page = int(page) if page else 1
    es = get_elastic()
    if not es:
        return HttpResponse()

    term = {}

    if group_id.startswith('test_id'):
        term = {"test_id" : group_id.replace('test_id_','')}
    else:
        term = { "uid" : group_id.replace('uid_','')}

    res = es.search(index="message-log", doc_type='message', body={
       "size": 50,
       "from" : 50*(page-1),
       "query": {
            "bool" : {
                "filter" : {
                    "term" : term
                }
            }
        },
       "sort": {
          "created": {
             "order": "desc"
          }
       }
    })

    messages = []
    previous = None
    for hit in res['hits']['hits'][::-1]:
        message = hit['_source']
        message['switch'] = previous != message['is_user']
        previous = message['is_user']
        response = message.get('response')
        elements = response.get('elements') if response else None
        if elements:
            message['elementWidth'] = len(elements)*215;
        message['json'] = json.dumps(message)
        messages.append(message)

    context = {'messages': messages}
    template = loader.get_template('botshot/log_conversation.html')
    return HttpResponse(template.render(context,request))

def debug(request):
    FacebookInterface.accept_request({'entry':[{'messaging':[{'message': {'seq': 356950, 'mid': 'mid.$cAAPhQrFuNkFibcXMZ1cPICEB8YUn', 'text': 'hi'}, 'recipient': {'id': '1092102107505462'}, 'timestamp': 1595663674471, 'sender': {'id': '1046728978756975'}}]}]})

    return HttpResponse('done')


def users_view(request):
    from botshot.models import User
    offset = int(request.GET.get("offset", 0))
    limit = int(request.GET.get("limit", 50))
    users = User.objects.all().order_by("uid")[offset:limit + offset]
    context = {"users": users, "next_offset": offset + limit, "prev_offset": offset - limit}
    return render(request, "botshot/users.html", context)
