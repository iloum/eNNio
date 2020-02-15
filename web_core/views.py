from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ennio_core.ennio_core import EnnIOCore
import re

RE_YOUTUBE_URL = re.compile("^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$")
RE_TIMESTAMP = re.compile("\d{2}:\d{2}")
ennio = EnnIOCore()

# Create your views here.
def home(request):
    return render(request, 'web_core/home.html', {'title': 'Home'})

def user_input(request):
    return render(request, 'web_evaluator/user-input.html', {'title': 'Input URL'})

@csrf_exempt
def results(request):
    url_input = request.POST.get('url_input', None)
    timestamp_input = request.POST.get('timestamp_input', None)

    # Check if the timestamp inserted is correct
    if not re.match(RE_TIMESTAMP, timestamp_input):
        data = {
            'error': True,
            'error_prompt': 'Please enter valid timestamp with the format mm:ss',
        }
        return JsonResponse(data)
    elif not re.match(RE_YOUTUBE_URL, url_input):
        data = {
            'error': True,
            'error_prompt': 'Please enter a valid Youtube URL',
        }
        return JsonResponse(data)
    else:
        path = ennio.live_ennio(url=url_input, start_time_str=timestamp_input)
        path = path.partition("data/")[2]

        # temp paths for debugging
        #path = "live/parsed/video/title_THE_2NIGHT_SHOW_-_--id_dYyBvUZ2ZxA-specs_256x144_25-from_0-to_20.mp4"
        data = {
            'error': False,
            'url': 'display?variable1='+path
        }
        return JsonResponse(data)


def display(request):
    path1 = request.GET.get('variable1', None)
    return render(request, 'web_core/results.html',
                  {'title': 'Display',
                   'path1': path1})


def about(request):
    return render(request, 'web_core/about.html',
                  {'title': 'About'})
