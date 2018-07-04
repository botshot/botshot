import json
from datetime import datetime

from django.conf import settings
from django.db.models import Max
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect

from botshot.core.responses import TextMessage
from .forms import MessageForm
from .interface import WebGuiInterface
from .models import WebMessageData


def webgui(request):
    if 'uid' not in request.session:
        return render(request, 'botshot/webchat/welcome.html')

    uid = request.session['uid']

    if request.method == 'POST':
        # message received via webgui
        if request.POST.get('message'):
            msg = WebMessageData()
            msg.uid = uid
            message_text = request.POST.get('message')
            msg.is_response = False
            msg.data = json.dumps(TextMessage(message_text).to_response())

            if message_text:
                # process message if text != null
                msg.save()
                if request.POST.get("postback"):
                    postback = request.POST.get("postback")
                    WebGuiInterface.accept_postback(msg, postback)
                else:
                    WebGuiInterface.accept_request(msg)
        else:
            print("Error, message not set in POST")
            return HttpResponseBadRequest()
        return HttpResponse()

    messages = WebMessageData.objects.filter(uid=uid).order_by('timestamp')
    context = {
        'uid': uid, 'messages': messages,
        'form': MessageForm, 'timestamp': datetime.now().timestamp(),
        'user_img': settings.BOT_CONFIG.get('WEBGUI_USER_IMAGE', 'images/icon_user.png'),
        'bot_img': settings.BOT_CONFIG.get('WEBGUI_BOT_IMAGE', 'images/icon_robot.png')
    }
    return render(request, 'botshot/webchat/index.html', context)


def do_login(request):
    if request.method == 'POST' and 'username' in request.POST:
        username = request.POST.get('username')
        uid = WebGuiInterface.make_uid(username)
        request.session['uid'] = uid
        request.session['username'] = username
        return HttpResponse()
    else:
        return HttpResponseBadRequest()


def do_logout(request):
    if 'uid' in request.session:
        WebGuiInterface.destroy_uid(request.session['uid'])
        del request.session['uid']
        del request.session['username']
    return redirect('webgui')


def get_last_change(request):
    if 'uid' in request.session:
        uid = request.session['uid']
        max_timestamp = WebMessageData.objects.filter(uid=uid).aggregate(Max('timestamp'))
        return JsonResponse(max_timestamp)
    return HttpResponseBadRequest()
