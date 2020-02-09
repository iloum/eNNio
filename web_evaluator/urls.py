from django.urls import path
from . import views
from django.conf.urls.static import static

from web_ui import settings

urlpatterns = [
    path('', views.home, name='evaluator-home'),
    path('input/', views.user_input, name='evaluator-input'),
    path('input/results/', views.results, name='evaluator-results'),
    path('input/display/', views.display, name='evaluator-disp'),
    path('wait/', views.wait, name='wait')
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)