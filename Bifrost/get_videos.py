#!/usr/bin/env python3

from pytube import YouTube
import numpy as np
import os
import re
from datetime import datetime,timedelta
import argparse
import shutil
import time
import csv
import json

def download_ytbvideo(Youtube_Link,output_folder,specs={"res":"144p","fps":30,"abr":"50kbps"},sleep=0):
    yt = YouTube(Youtube_Link)
    audio=yt.streams.filter(mime_type="audio/webm").filter(abr=specs['abr']).first()
    video=yt.streams.filter(mime_type="video/mp4").filter(res=specs['res'],fps=specs['fps']).first()
    try:    
        print("downloading movie clips..")
        filename_audio=audio.download(output_folder+"/downloaded/audio_streams/")
        filename_video=video.download(output_folder+"/downloaded/video_streams/")
        print("got audio and video files")
        if sleep:
            print("sleeping for "+sleep)
            time.sleep(sleep)
    except Exception as e:
        print("Oops! something went wrong!",e)
    return filename_audio,filename_video

def cutout(input_file,timestamps,output_folder,stream_type="v"):
    """
    Takes a list of pairs of timestamps. Each pair corresponds to a scene that should be removed from the final mp4 video.
    It uses ffmpeg library to cut and split the input into either a video or audio stream (v for video and a for audio). 
    """
    if shutil.which("ffmpeg"):
        pass
    else:
        raise RuntimeError('ffmpeg not found in the system.')
    if stream_type=="v":
        trim_type="trim"
    elif stream_type=="a":
        trim_type="atrim"
    if stream_type=="v":
        setpts_type="setpts"
    elif stream_type=="a":
        setpts_type="asetpts"
    num_segments=len(timestamps)
    build_concats=f'ffmpeg -y -i {input_file} -filter_complex "'
    for i,(a,b) in enumerate(timestamps):
         build_concats+=f"[0:{stream_type}]{trim_type}=start={a}:end={b},{setpts_type}=PTS-STARTPTS[{i}];"
         if(i==1 and stream_type=="v"):
            build_concats+=f"[0][{i}]concat[{i}out];"
         elif(i==1 and stream_type=="a"):
            build_concats+=f"[0][{i}]concat=v=0:a=1[{i}out];"
         elif(i%1==0 and i!=0 and stream_type=="v"):
            build_concats+=f"[{i-1}out][{i}]concat[{i}out];"
         elif(i%1==0 and i!=0 and stream_type=="a"):
            build_concats+=f"[{i-1}out][{i}]concat=v=0:a=1[{i}out];"
    #remove the last semicolon.
    build_concats=build_concats[:-1]
    output_file=input_file.split("/")[-1]
    build_concats+=f'" -map [{i}out] '+f'"{output_folder}/{output_file}'
    os.system(build_concats)
    
def join_streams(audio_stream,video_stream,output_file):
    """
    joints two streams together in one mp4 file.
    """
    if shutil.which("ffmpeg"):
        pass
    else:
        raise RuntimeError('ffmpeg not found in the system.')
    go_join=f"""ffmpeg -y -i {audio_stream} -i {video_stream} \
    -c copy {output_file}"""
    os.system(go_join)

    
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = 'Welcome to Bifröst wanderer. To cross, you have to sacrifice youtube videos.')
    parser.add_argument('-f',"--filename",type=str,help="provide a csv file to read the youtube links, the 'cutout' timestamps and optionaly the download specs for the video")
    parser.add_argument('-o',"--outputfolder",type=str,help="path were files will be stored")
    args = parser.parse_args()
    
    persisted_meta={}
    persisted_meta_f=args.outputfolder+"/.youtubelinks_meta"
    if os.path.exists(persisted_meta_f):
        with open(persisted_meta_f) as f:
            persisted_meta=json.loads(f.read())

    with open(args.filename) as csv_file:
       
        csv_data = csv.DictReader(csv_file, delimiter='\t')
        for item in csv_data:
            item['timestamps']=eval(item['timestamps'])
            item['specs']=eval(item['specs'])
            
            if item['link'] in persisted_meta.keys():
                persisted_item = persisted_meta[item['link']]
                changed=False
                if item['specs']:
                    if item['specs']!=persisted_item['specs']:
                        persisted_item['specs']=item['specs']
                        print("video "+item['link']+"... was downloaded before with different specs, replacing video using new specs...")
                        filename=download_ytbvideo(item['link'],args.outputfolder,specs=item['specs'])
                
                if item['timestamps']:
                    item['timestamps']=eval(item['timestamps'])
                    item['timestamps'].sort()
                    if item['timestamps']!=persisted_item['timestamps']:
                        persisted_item['timestamps']=item['timestamps']
                        print("given video "+tsamps+"... was downloaded before with different tsamps, replacing video...")
                        cutout(item['link'],item['timestamps'],args.outputfolder,stream_type="v")
                        cutout(item['link'],item['timestamps'],args.outputfolder,stream_type="a")
                        
            else:
                if item['specs']:
                    filename_audio,filename_video=download_ytbvideo(item['link'],args.outputfolder,specs=item['specs'])
                else:
                    filename_audio,filename_video=download_ytbvideo(item['link'],args.outputfolder)
                if item['timestamps']:
                    cutout(filename_audio,item['timestamps'],args.outputfolder+"/video/",stream_type="a")
                    cutout(filename_video,item['timestamps'],args.outputfolder+"/audio/",stream_type="v")
                else:
                    shutil.copyfile(filename_video,args.outputfolder+"/audio/"+filename_video.split("/")[-1])
                    shutil.copyfile(filename_audio,args.outputfolder+"/audio/"+filename_audio.split("/")[-1])
                
                persisted_meta[item['link']]={"timestamps":item['timestamps'],'specs':item['specs']}
                              
        with open(persisted_meta_f,'w') as f:
            writer=f.write(json.dumps(persisted_meta))