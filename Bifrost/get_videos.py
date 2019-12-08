#!/usr/bin/env python3

import numpy as np
import os
import re
from datetime import datetime,timedelta
import argparse
import shutil
import time
import csv
import json
import subprocess as subp
import sys


def download_ytbvideo(Youtube_Link,output_folder,specs={"res":144,"fps":30,"abr":50},sleep=0):
    
    aoutput_template=os.path.join(output_folder,"audio/",r"%(title)s-%(id)s.%(ext)s")
    voutput_template=os.path.join(output_folder,"video/",r"%(title)s-%(id)s.%(ext)s")
    vdl_command= ' -o "{output_template}"  --restrict-filenames -f "bestvideo[height<={res}][fps<={fps}]" "{link}"'
    adl_command= ' -o "{output_template}"  --restrict-filenames -f "bestaudio[abr<={abr}]" "{link}"'

    print("preparing download of video and audio ...")
    
    try:    
        voutput_dlcommand=vdl_command.format(link=Youtube_Link,output_template=voutput_template,res=specs['res'],fps=specs['fps'])
        voutput=subp.check_output(
            "youtube-dl"+voutput_dlcommand  
                ,stderr=sys.stderr,shell=True).decode("utf-8")
        
        checkfor_video=re.findall(".*\[download\] (.*) has already.*",voutput)

        if checkfor_video:
            print("video is allready available!")
            filename_video=checkfor_video[0]
        else:
            print("downloaded video")
            filename_video=re.findall("Destination.*?\n",voutput)[0].split("Destination:")[1].strip()

    except Exception as e:
        print("Oops! something went wrong while downloading video!",e)

    try: 

        aoutput_dlcommand=adl_command.format(link=Youtube_Link,output_template=aoutput_template,abr=specs['abr'])
        aoutput=subp.check_output(
            "youtube-dl"+aoutput_dlcommand,
            stderr=sys.stderr,shell=True).decode("utf-8")

        checkfor_audio=re.findall(".*\[download\] (.*) has already.*",aoutput)

        if checkfor_audio:
            print("audio is allready available!")
            filename_audio=checkfor_audio[0]
        else:
            print("downloaded audio")
            filename_audio=re.findall("Destination.*?\n",aoutput)[0].split("Destination:")[1].strip()

    except Exception as e:
        print("Oops! something went wrong while downloading audio!",e)
        
    if sleep:
        print("sleeping for "+sleep)
        time.sleep(sleep)

    return filename_audio,filename_video

def cutout(input_file,timestamps,output_folder,stream_type="v",concatenate=False,Execute=True):
    """
    Takes a list of pairs of timestamps. Each pair corresponds to a scene that should be removed from the final mp4 video.
    It uses ffmpeg library to cut and split the input into either a video or audio stream (v for video and a for audio). 
    """

    outfilenames=[]

    logs_path=os.path.join(output_folder,"ffmpeg_logs.txt")
    
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


    if concatenate:
        build_concats=f'ffmpeg -y -i "{input_file}" -filter_complex "'
        for i,(a,b) in enumerate(timestamps):
            build_concats+=f"[0:{stream_type}]{trim_type}=start={a}:end={b},{setpts_type}=PTS-STARTPTS[s{i}];"
        
        if num_segments>1: 
            streams="".join(["[s%s]"%(i) for i in range(num_segments)]) 
            if(stream_type=="v"):
              build_concats+=f"{streams}concat=v=1:a=0[out];"
            elif(stream_type=="a"):
              build_concats+=f"{streams}concat=v=0:a=1[out];"

        #remove the last semicolon.
        build_concats=build_concats[:-1]
       
        filename=input_file.split("/")[-1]
        filename_parts=filename.split(".")
        new_filename=filename_parts[-2]+"_"+"_".join(["from:"+str(a)+"-"+"to:"+str(b) for a,b in timestamps])+"."+filename_parts[-1]
        output_file=os.path.join(output_folder,new_filename)
        outfilenames.append(new_filename)

        if num_segments>1:
            build_concats+=f'" -map [out] '+f'"{output_file}"'
        else:
            build_concats+=f'" -map [s0] '+f'"{output_file}"'
        if Execute:
            with open(logs_path,"a") as logs:
                subp.check_call(
                build_concats,stdout=logs,
                stderr=logs,shell=True)
    else:
        for i,(a,b) in enumerate(timestamps):
            build_concats=f'ffmpeg -y -i "{input_file}" -filter_complex "'
            build_concats+=f"[0:{stream_type}]{trim_type}=start={a}:end={b},{setpts_type}=PTS-STARTPTS[s0];"
    
            #remove the last semicolon.
            build_concats=build_concats[:-1]

            filename=input_file.split("/")[-1]
            filename_parts=filename.split(".")
            new_filename=filename_parts[-2]+"_"+"from:"+str(a)+"-"+"to:"+str(b)+"."+filename_parts[-1]
            output_file=os.path.join(output_folder,new_filename)
            outfilenames.append(new_filename)
           
            if num_segments>1 and concatenate:
                build_concats+=f'" -map [out] '+f'"{output_file}"'
            else:
                build_concats+=f'" -map [s0] '+f'"{output_file}"'
            if Execute:
               with open(logs_path,"a") as logs:
                subp.check_call(
                build_concats,stdout=logs,
                stderr=logs,shell=True)

    return outfilenames
        
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


def compareflat_dict(dict1,dict2):
    '''
    compares if two dicts. If all keys and values of dict1 match with a subset of those of dict2 then 
    dict1 <= dict2
    '''
    for key1 in dict1.keys():
        if key1 in dict2.keys():
            if dict1[key1]!=dict2[key1]:
                return False
    return True

def create_folder(folderdest):
    
    if not os.path.exists(folderdest):
        print("creating folder ",folderdest,"...")
        os.mkdir(folderdest)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = 'Welcome to Bifröst wanderer. To cross, you have to sacrifice youtube videos.')
    parser.add_argument('-f',"--filename",type=str,help="provide a csv file to read the youtube links, the 'cutout' timestamps and optionaly the download specs for the video")
    parser.add_argument('-o',"--outputfolder",type=str,help="path were files will be stored")
    args = parser.parse_args()

    downloads_folder=os.path.join(args.outputfolder,"downloaded/")
    parsed_folder=os.path.join(args.outputfolder,"parsed/")

    create_folder(downloads_folder)
    create_folder(parsed_folder)
    create_folder(os.path.join(downloads_folder,"audio/"))
    create_folder(os.path.join(downloads_folder,"video/"))
    create_folder(os.path.join(parsed_folder,"audio/"))
    create_folder(os.path.join(parsed_folder,"video/"))
    
    
    persisted_meta_f=os.path.join(args.outputfolder,".youtubelinks_meta")
    if os.path.exists(persisted_meta_f):
        with open(persisted_meta_f) as f:
            persisted_meta=json.loads(f.read())
    else:
        print("creating a metadata file")
        persisted_meta={}
    
    with open(args.filename) as csv_file:
       
        csv_data = csv.DictReader(csv_file, delimiter='|')
        for rawitem in csv_data:
            print("\n\n")
            print("*** processing link ", rawitem['link']," ***")
            #flag to compare specs
            skip_download=False
            skip_videoparsing=False

            default_specs={"res":144,"fps":30,"abr":50}

            parsed_item={}
            parsed_item['link']=rawitem['link']

            if rawitem['res'] or rawitem['fps'] or rawitem['abr']:
                parsed_item['specs']={'res':rawitem['res'],'fps':int(rawitem['fps']),'abr':rawitem['abr']}
            else:
                parsed_item['specs']=default_specs

            if rawitem['timestamps']:
                timestamps_provided=True
                parsed_item['timestamps']=eval(rawitem['timestamps'])
                parsed_item['timestamps'].sort()
            else:
                parsed_item['timestamps']=[]
            
            if rawitem['concatenate']:
                OPT_CONCAT=eval(rawitem['concatenate'])
            else:
                OPT_CONCAT=False

            #checks if current parsed_item is in previously downloaded rawitems
            if persisted_meta and (parsed_item['link'] in persisted_meta.keys()):
                
                persisted_item = persisted_meta[parsed_item['link']]
                filename_audio=persisted_item['filenames']['downloaded_audio']
                filename_video=persisted_item['filenames']['downloaded_video']
                
                if compareflat_dict(parsed_item['specs'],persisted_item['specs']):
                    skip_download=True
                    skip_videoparsing=True

                if parsed_item['timestamps']:
                    # get the names without executing
                    parsed_video_filenames=cutout(filename_video,parsed_item['timestamps'],os.path.join(parsed_folder,"video/"),stream_type="v",concatenate=OPT_CONCAT,Execute=False)
                    parsed_audio_filenames=cutout(filename_audio,parsed_item['timestamps'],os.path.join(parsed_folder,"audio/"),stream_type="a",concatenate=OPT_CONCAT,Execute=False)
                    video_paths_exist = all([os.path.exists(os.path.join(parsed_folder,"video/",path)) for path in parsed_video_filenames])
                    audio_paths_exist = all([os.path.exists(os.path.join(parsed_folder,"audio/",path)) for path in parsed_audio_filenames])
                    
                    if not video_paths_exist or \
                    not audio_paths_exist or \
                    not set(parsed_video_filenames).issubset(persisted_item['filenames']['parsed_video']) or \
                    not set(parsed_audio_filenames).issubset(persisted_item['filenames']['parsed_audio']):
                        skip_videoparsing=skip_videoparsing and False

            if not skip_download:
                filename_audio,filename_video=download_ytbvideo(parsed_item['link'],downloads_folder,parsed_item['specs'])
            else: 
                print("skipping video download, files are allready available as:\n\t\t","\n\t\t".join(parsed_video_filenames+parsed_audio_filenames))
                
            if not skip_videoparsing:     
                if parsed_item['timestamps']:
                    #rawitem['timestamps']=eval(rawitem['timestamps'])
                    parsed_video_filenames=cutout(filename_video,parsed_item['timestamps'],os.path.join(parsed_folder,"video/"),stream_type="v",concatenate=OPT_CONCAT)
                    parsed_audio_filenames=cutout(filename_audio,parsed_item['timestamps'],os.path.join(parsed_folder,"audio/"),stream_type="a",concatenate=OPT_CONCAT)
                else:
                    shutil.copyfile(filename_video,os.path.join(parsed_folder,"video/",filename_video.split("/")[-1]))
                    shutil.copyfile(filename_audio,os.path.join(parsed_folder,"audio/",filename_audio.split("/")[-1]))
            else:
                print("skipping audio parsing, files are allready have those timestamps tracked as:\n\t\t","\n\t\t".join(parsed_video_filenames+parsed_audio_filenames))

            parsed_item['filenames']={"downloaded_audio":filename_audio,"downloaded_video":filename_video,
            "parsed_video":parsed_video_filenames,"parsed_audio":parsed_audio_filenames}
            
            if persisted_meta.get(parsed_item['link']) and skip_download:
                persisted_meta[parsed_item['link']]['filenames']['parsed_video'].extend(parsed_video_filenames)
                persisted_meta[parsed_item['link']]['filenames']['parsed_audio'].extend(parsed_audio_filenames)
            else:
                persisted_meta[parsed_item['link']]={
                "link":parsed_item['link'],
                'specs':parsed_item['specs'],
                'filenames':parsed_item['filenames']
                }

            with open(persisted_meta_f,'w') as f:
                writer=f.write(json.dumps(persisted_meta))