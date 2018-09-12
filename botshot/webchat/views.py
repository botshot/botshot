import json
from datetime import datetime

from django.conf import settings
from django.db.models import Max
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect

from botshot.core.responses import TextMessage
from .forms import MessageForm


def webchat(request):
    if 'uid' not in request.session:
        return render(request, 'botshot/webchat/welcome.html')

    uid = request.session['uid']

    if request.method == 'POST':
        # message received via webchat
        if request.POST.get('message'):
            message_text = request.POST.get('message')
            #data = json.dumps(TextMessage(message_text).to_response())

            msg = WebMessageData.objects.create(uid=uid, is_response=False, data=data)

            # process message if text != null
            msg.save()
            if request.POST.get("postback"):
                postback = request.POST.get("postback")
                WebchatInterface.accept_postback(msg, postback)
            else:
                WebchatInterface.accept_request(msg)
        else:
            print("Error, message not set in POST")
            return HttpResponseBadRequest()
        return HttpResponse()

    messages = WebMessageData.objects.filter(uid=uid).order_by('timestamp')
    context = {
        'uid': uid, 'messages': messages,
        'form': MessageForm, 'timestamp': datetime.now().timestamp(),
        'user_img': settings.BOT_CONFIG.get('WEBCHAT_USER_IMAGE', 'images/icon_user.png'),
        'bot_img': settings.BOT_CONFIG.get('WEBCHAT_BOT_IMAGE', 'images/icon_robot.png')
    }
    return render(request, 'botshot/webchat/index.html', context)


def do_login(request):
    if request.method == 'POST' and 'username' in request.POST:
        username = request.POST.get('username')
        uid = WebchatInterface.make_uid(username)
        request.session['uid'] = uid
        request.session['username'] = username
        return HttpResponse()
    else:
        return HttpResponseBadRequest()


def do_logout(request):
    if 'uid' in request.session:
        WebchatInterface.destroy_uid(request.session['uid'])
        del request.session['uid']
        del request.session['username']
    return redirect('webchat')


def get_last_change(request):
    if 'uid' in request.session:
        uid = request.session['uid']
        max_timestamp = WebMessageData.objects.filter(uid=uid).aggregate(Max('timestamp'))
        timestamp = max_timestamp.get('timestamp__max')
        timestamp = timestamp.timestamp() if timestamp else 0
        return JsonResponse({'timestamp__max': timestamp})
    return HttpResponseBadRequest()
