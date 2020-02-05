from django.shortcuts import render
from django.http import HttpResponse


def home(request):
    return render(request, 'web_evaluator/home.html', {'title': 'Evaluation Home'})


def user_input(request):
    return render(request, 'web_evaluator/user-input.html', {'title': 'Input URL'})


def wait(request):
    return render(request, 'web_evaluator/wait.html', {'title': 'Please Wait...'})