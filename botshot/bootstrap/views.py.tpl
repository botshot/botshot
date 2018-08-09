from django.http import HttpResponse
from django.template import loader

def landing(request):
    # template = loader.get_template('landing.html')
    # template.render({}, request)

    return HttpResponse('Landing page :) TODO: add main app templates dir to settings.py templates dirs.')
