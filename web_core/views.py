from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import re

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
        videopath1 = "_1_11_12_Movie_CLIP_-_Showdown_at_the_House_of_Blue_Leaves_2003_HD-id_EajaioMj-NA-specs_256x144_24-from_80-to_100.mp4"
        data = {
            'error': False,
            'url': 'display?variable1='+videopath1+'&variable2=2',
        }
        return JsonResponse(data)


def display(request):
    var1 = request.GET.get('variable1', None)
    var2 = request.GET.get('variable2', None)
    return render(request, 'web_evaluator/results.html', {'title': 'Display', 'var1': var1, 'var2': var2})
