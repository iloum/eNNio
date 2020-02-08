from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from ennio_exceptions import VideoAlreadyExist
import re


RE_TIMESTAMP = re.compile("\d{2}:\d{2}")

def home(request):
    return render(request, 'web_evaluator/home.html', {'title': 'Evaluation Home'})


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
    else:
        data = {
            'error': False,
            'url': 'evaluator-results',
        }
        return JsonResponse(data)
#    try:
#        pass
#    except VideoAlreadyExist:
#        pass
# Kanw logikous elegxous sta data




def wait(request):
    return render(request, 'web_evaluator/wait.html', {'title': 'Please Wait...'})