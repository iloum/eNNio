from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def home(request):
    return render(request, 'web_evaluator/home.html', {'title': 'Evaluation Home'})


def user_input(request):
    return render(request, 'web_evaluator/user-input.html', {'title': 'Input URL'})

@csrf_exempt
def hello_world(request):
    url_input = request.POST.get('url_input', None)
    text_input = request.POST.get('text_input', None)
    #Kanw logikous elegxous sta data


    data = {
        'error': True,
        'response': 'Hey Touros',
    }
    return JsonResponse(data)

def wait(request):
    return render(request, 'web_evaluator/wait.html', {'title': 'Please Wait...'})