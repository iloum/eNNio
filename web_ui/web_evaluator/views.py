from django.shortcuts import render
from django.http import HttpResponse


def home(request):
    return HttpResponse('<h1>Thanks for helping us make ennIO better. Let\'s get started!</h1>')

def user_input(request):
    return HttpResponse('<h1> Please input your Youtube URL</h1>')
