from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='evaluator-home'),
    path('input/', views.user_input, name='evaluator-input'),
    path('input/results/', views.results, name='evaluator-results'),
    path('input/display/', views.display, name='evaluator-disp'),
    path('wait/', views.wait, name='wait')
]