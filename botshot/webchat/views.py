import json
from datetime import datetime

from django.conf import settings
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import render, redirect
from botshot.core.chat_session import ChatSession
from botshot.webchat.interface import WebchatInterface
from botshot.models import MessageLog
from .forms import MessageForm
import logging

def webchat(request):
    if request.method == 'POST':
        if request.POST.get('message'):
            text = request.POST.get('message')
            raw_message = {'text': text}
            if request.POST.get('payload'):
                raw_message['payload'] = json.loads(request.POST.get('payload'))
        else:
            print("Error, message not set in POST")
            return

        if 'webchat_id' not in request.session:
            webchat_id = WebchatInterface.make_webchat_id()
            request.session['webchat_id'] = webchat_id

        webchat_id = request.session['webchat_id']
        interface = WebchatInterface(webchat_id=webchat_id)
        logging.info('[WEBCHAT] Received message from {}: {}'.format(webchat_id, raw_message))
        session = ChatSession(interface)
        session.accept(raw_message)
        return JsonResponse({'ok': True})

    if 'webchat_id' in request.session:
        messages = _get_webchat_id_messages(request.session['webchat_id'])
    else:
        default_msg = MessageLog()
        default_msg.is_from_user = False
        default_msg.time = datetime.now()
        default_msg.message_type = 'default'
        default_msg.text = 'Hi there, this is the default greeting message!'
        messages = [default_msg]

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
    interface = WebchatInterface(webchat_id=webchat_id)
    chat_id = ChatSession.create_chat_id(interface)
    return MessageLog.objects.filter(chat_id=chat_id).order_by('time')


def get_last_change(request):
    if 'webchat_id' not in request.session:
        max_timestamp = 0
    else:
        webchat_id = request.session['webchat_id']
        max_timestamp = _get_webchat_id_messages(webchat_id).aggregate(Max('time')).get('time__max')
        max_timestamp = max_timestamp.timestamp() if max_timestamp else 0
    return JsonResponse({'timestamp': max_timestamp})

