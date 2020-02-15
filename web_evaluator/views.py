from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ennio_core.ennio_core import EnnIOCore
from ennio_exceptions import VideoAlreadyExist
import re

RE_YOUTUBE_URL = re.compile("^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$")
RE_TIMESTAMP = re.compile("\d{2}:\d{2}")
ennio = EnnIOCore()

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
    elif not re.match(RE_YOUTUBE_URL, url_input):
        data = {
            'error': True,
            'error_prompt': 'Please enter a valid Youtube URL',
        }
        return JsonResponse(data)
    else:
        video_id, paths = ennio.evaluation_mode(url=url_input, start_time_str=timestamp_input)
        path1 = paths[0].partition("data/")[2]
        path2 = paths[1].partition("data/")[2]
        path3 = paths[-1].partition("data/")[2]
        #path4 = paths[3]
        # temp paths for debugging
        #path1 = "_1_11_12_Movie_CLIP_-_Showdown_at_the_House_of_Blue_Leaves_2003_HD-id_EajaioMj-NA-specs_256x144_24-from_80-to_100.mp4"
        #path2 = "_1_11_12_Movie_CLIP_-_Showdown_at_the_House_of_Blue_Leaves_2003_HD-id_EajaioMj-NA-specs_256x144_24-from_80-to_100.mp4"
        #path3 = "_1_11_12_Movie_CLIP_-_Showdown_at_the_House_of_Blue_Leaves_2003_HD-id_EajaioMj-NA-specs_256x144_24-from_80-to_100.mp4"
        #path4 = "_1_11_12_Movie_CLIP_-_Showdown_at_the_House_of_Blue_Leaves_2003_HD-id_EajaioMj-NA-specs_256x144_24-from_80-to_100.mp4"
        data = {
            'error': False,
            'url': 'display?videoid='+video_id+'&variable1='+path1+'&variable2='+path2+'&variable3='+path3#+'&variable4='+path4
        }
        return JsonResponse(data)

@csrf_exempt
def display(request):
    path1 = request.GET.get('variable1', None)
    path2 = request.GET.get('variable2', None)
    path3 = request.GET.get('variable3', None)
    path4 = request.GET.get('variable4', None)
    video_id = request.GET.get('videoid', None)
    return render(request, 'web_evaluator/results.html',
                  {'title': 'Display',
                   'path1': path1,
                   'path2': path2,
                   'path3': path3,
                   'path4': path4,
                   'videoid': video_id})

@csrf_exempt
def vote(request):
    video_id = request.POST.get('videoid', None)
    path = request.POST.get('path', None)
    model = path.partition('merged/')[2].strip('.mp4')
    ennio.update_evaluation_vote(video_id=video_id, winner=path)
    data = {
        'error': False,
        'url': 'thanks?videoid=' + video_id + '&model=' + model
    }
    return JsonResponse(data)


def thanks(request):
    video_id = request.GET.get('videoid', None)
    model = request.GET.get('model', None)
    return render(request, 'web_evaluator/thanks.html', {'title': 'Thank you...',
                                                         'video': video_id,
                                                         'model': model})
