from django.urls import path
from . import views
from django.conf.urls.static import static

from web_ui import settings

urlpatterns = [
    path('', views.home, name='core-home'),
    path('input/', views.user_input, name='core-input'),
    path('input/results/', views.results, name='core-results'),
    path('input/display/', views.display, name='core-disp')
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)