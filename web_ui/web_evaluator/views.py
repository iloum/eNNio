from django.shortcuts import render
from django.http import HttpResponse


def home(request):
    return render(request, 'web_evaluator/home.html')


def user_input(request):
    return render(request, 'web_evaluator/user-input.html')
