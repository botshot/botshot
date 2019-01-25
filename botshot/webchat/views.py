import json
from datetime import datetime

from django.conf import settings
from django.db.models import Max
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect

from botshot.models import ChatMessage
from botshot.webchat.interface import WebchatInterface
from .forms import MessageForm
import logging


def webchat(request):
    if request.method == 'POST':
        if not request.POST.get('message'):
            print("Error, message not set in POST")
            return HttpResponse(400)

        if 'webchat_id' not in request.session:
            webchat_id = WebchatInterface.make_webchat_id()
            request.session['webchat_id'] = webchat_id

        interface = WebchatInterface()
        is_ok = interface.webhook(request)
        return JsonResponse({'ok': True}) if is_ok else HttpResponse(400)

    if 'webchat_id' in request.session:
        messages = _get_webchat_id_messages(request.session['webchat_id'])
    else:
        messages = []
        welcome_msg = settings.BOT_CONFIG.get(
            'WEBCHAT_WELCOME_MESSAGE',
            'Hi there, this is the default greeting message!'
        )
        if welcome_msg:
            default_message = ChatMessage()
            default_message.type = ChatMessage.MESSAGE
            default_message.text = welcome_msg
            default_message.time = datetime.now()
            default_message.is_user = False
            messages.append(default_message)

    context = {
        'messages': messages,
        'form': MessageForm,
        'timestamp': datetime.now().timestamp(),
        'user_img': settings.BOT_CONFIG.get('WEBCHAT_USER_IMAGE', 'images/icon_user.png'),
        'bot_img': settings.BOT_CONFIG.get('WEBCHAT_BOT_IMAGE', 'images/icon_robot.png')
    }
    return render(request, 'botshot/webchat/index.html', context)


def do_logout(request):
    if 'webchat_id' in request.session:
        del request.session['webchat_id']
    return redirect('webchat')


def _get_webchat_id_messages(webchat_id):
    return ChatMessage.objects.filter(conversation__raw_conversation_id=webchat_id).order_by('time')


def get_last_change(request):
    if 'webchat_id' not in request.session:
        max_timestamp = 0
    else:
        webchat_id = request.session['webchat_id']
        max_timestamp = _get_webchat_id_messages(webchat_id).aggregate(Max('time')).get('time__max')
        max_timestamp = max_timestamp.timestamp() if max_timestamp else 0
    return JsonResponse({'timestamp': max_timestamp})
