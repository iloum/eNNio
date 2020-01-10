import subprocess as subp
import shutil
import numpy as np
import os
import re
from datetime import datetime,timedelta
import time
import sys
import numbers

from collections import Sequence
from itertools import chain, count


def filepath_exists(path_members,filename):
    return os.path.exists(os.path.join(*path_members,filename)) 

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

def compare_lists(list1,list2):
    '''
    Checks if all elements of list1 are elements of list2.
    '''
    for item in list1:
        if item in list2:
            pass
        else:
            return False
    return True

def remove_file(filepath):
    if os.path.isfile(filepath):
        try: 
            os.remove(filepath) 
            return True 
        except OSError as error: 
            print(error)
            print("wont be able to save bad input...")
            return False

def create_folder(folderdest):
    
    if not os.path.exists(folderdest):
        print("creating folder ",folderdest,"...")
        os.mkdir(folderdest)

def convert_timestamps(timestamps):
    depth_timestamps=depth(timestamps)
    returned_list=[]
    if depth_timestamps!=0:
        for i in range(len(timestamps)):
            returned_list.append(convert_timestamps(timestamps[i]))
        return returned_list
    else:
        timestamps=minutes_toseconds(timestamps)
        return timestamps

def timestamp_input_parser(timestamps):
    '''
    parses a string of the form [[0:20,0:30]] to one of the form [["0:20","0:30"]]
    '''
    return re.sub("(([0-9]+:){0,2}[0-9]+)",r'"\1"',timestamps)

def minutes_toseconds(clocktime):
    '''
    converts datetime formats H:M:S,M:S,S to seconds up to 23:59:59
    '''
    if  isinstance(clocktime, numbers.Number):
        return clocktime
    valid_pattern=re.match("^([0-9]+:){0,2}?[0-9]+$",clocktime)
    if valid_pattern:
        pass
    else:
        raise Exception("invalid datetime pattern detected please use H:M:S,M:S or S")
    timesplits=len(clocktime.split(":"))
    if timesplits==1:
        format_str="%S"
    elif timesplits==2:
        format_str="%M:%S"
    elif timesplits==3:
        format_str="%H:%M:%S"        
    seconds = (datetime.strptime(clocktime, format_str)-datetime.strptime("00:00","%M:%S")).total_seconds()
    return int(seconds)


def depth(seq):
    max_depth=0
    if hasattr(seq,"__iter__") and not isinstance(seq,str):
        for i in seq:
            max_depth=max(max_depth,depth(i))
        return max_depth+1
    else:
        return max_depth
    

def cropper(source_filename,filetype,timestamps,path_members,threads):

    if filetype=="video":
        stream_type="v"
    elif filetype=="audio":
        stream_type="a"
    else:
        raise Exception("unkwown filetype, pick one from audio or video..")
    

    parsed_filenames=[]
    for timestamp in timestamps:

        if filetype=="video":
            filename=get_filename(os.path.basename(source_filename),timestamp,"mp4")
        elif filetype=="audio":
            filename=get_filename(os.path.basename(source_filename),timestamp,"wav")
        else:
            filename=get_filename(os.path.basename(source_filename),timestamp)

        if filepath_exists(path_members,filename):
            print(filetype,"already available for timestamps",timestamp,"..")
        else:
            print("cropping ",filetype," using timestamps",timestamp,"...")

            if timestamp=="nocuts":
                shutil.copyfile(filename,os.path.join(*path_members,new_filename))
            else:
                cutout(source_filename,timestamp,os.path.join(*path_members),stream_type,threads)

        parsed_filenames.append(filename)
    return parsed_filenames

def get_filename(input_file,timestamps,ext=None):
        '''
        returns the filename, if provided the extension will overwrite the previous file extension
        '''
        outfilenames=[]
        filename=os.path.basename(input_file)
        filename_parts=filename.split(".")

        if ext:
            filename_parts[-1]=ext

        if timestamps=="nocuts":
            new_filename=filename_parts[-2]+"_nocuts"+"."+filename_parts[-1]
        else:
            
            listdepth=depth(timestamps)

            if listdepth==2:
                new_filename=filename_parts[-2]+"-"+"_".join(["from_"+str(a)+"-"+"to_"+str(b) for a,b in timestamps])+"."+filename_parts[-1]
            else:
                a,b=timestamps
                new_filename=filename_parts[-2]+"-from_"+str(a)+"-"+"to_"+str(b)+"."+filename_parts[-1]

        return new_filename


def download_ytbvideo(Youtube_Link,filetype,output_folder,specs={"res":144,"fps":30,"abr":50},sleep=0):

    if sleep:
        print("sleeping for "+sleep)
        time.sleep(sleep)
    
    aoutput_template=os.path.join(output_folder,"audio/",r"title_%(title)s-id_%(id)s-specs_%(abr)s.%(ext)s")
    voutput_template=os.path.join(output_folder,"video/",r"title_%(title)s-id_%(id)s-specs_%(resolution)s_%(fps)s.%(ext)s")
    vdl_command= ' -o "{output_template}"  --restrict-filenames -f "bestvideo[height<={res}][fps<={fps}]" "{link}"'
    adl_command= ' -o "{output_template}"  --restrict-filenames -f "bestaudio[abr<={abr}]" "{link}"'

    if filetype=="v":
        get_video=True
        get_audio=False
    elif filetype=="a":
        get_video=False
        get_audio=True
    else:
        raise Exception("unkown filetype",filetype)

    if get_video:

        voutput_dlcommand=vdl_command.format(link=Youtube_Link,output_template=voutput_template,res=specs['res'],fps=specs['fps'])
        process=subp.run("youtube-dl -i "+voutput_dlcommand,capture_output=True,shell=True)
        process_error=process.stderr.decode("utf-8")

        if process_error:

            print(process_error)

            if re.match(".*format.*",process_error):
                if re.match(".*format.*",str(e)):
                    voutput=subp.check_output(
                    "youtube-dl {link} -F".format(link=Youtube_Link),
                    stderr=sys.stderr,shell=True).decode("utf-8")
               
                raise Exception("Problem while downloading video, probably format issue"+\
                    "you used res:{res}, fps:{fps}".format(res=specs["res"],fps=specs["fps"]) +\
                    "here are the available formats"+\
                    voutput)
            else:
                raise Exception(process_error)

        process_output = process.stdout.decode("utf-8")
        checkfor_video=re.findall(".*\[download\] (.*) has already.*",process_output)

        if checkfor_video:
            print("video is already available!")
            filename=checkfor_video[0]
        else:
            print("downloaded video")
            filename=re.findall("Destination.*?\n",process_output)[0].split("Destination:")[1].strip()

        return filename

            
    elif get_audio:
        
        aoutput_dlcommand=adl_command.format(link=Youtube_Link,output_template=aoutput_template,abr=specs['abr'])
        process=subp.run("youtube-dl -i "+aoutput_dlcommand,capture_output=True,shell=True)
        process_error=process.stderr.decode("utf-8")

        if process_error:
            print(process_error)
            if re.match(".*format.*",process_error):
                aoutput=subp.check_output(
                    "youtube-dl {link} -F".format(link=Youtube_Link),
                    stderr=sys.stderr,shell=True).decode("utf-8")

                raise Exception("Problem while downloading audio, probably format issue"+\
                    "you used abr:{abr}".format(abr=specs["abr"]) +\
                    "here are the available formats"+\
                    aoutput)
            else:
                raise Exception(process_error)

        process_output = process.stdout.decode("utf-8")

        checkfor_audio=re.findall(".*\[download\] (.*) has already.*",process_output)

        if checkfor_audio:
            print("audio is already available!")
            filename=checkfor_audio[0]
        else:
            print("downloaded audio")
            filename=re.findall("Destination.*?\n",process_output)[0].split("Destination:")[1].strip()
        
       

        return filename
        
       
        
            

def cutout(input_file,timestamps,output_folder,stream_type="v",Execute=True,threads=2):
    """
    Takes a list of pairs of timestamps. Each pair corresponds to a scene that should be removed from the final mp4 video.
    It uses ffmpeg library to cut and split the input into either a video or audio stream (v for video and a for audio). 
    """

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
    depth_list=depth(timestamps)

    if depth_list>1 and len(timestamps)>1:
   
        build_concats=f'ffmpeg -threads {threads} -y -i "{input_file}" -filter_complex "'
        for i,(a,b) in enumerate(timestamps):
            build_concats+=f"[0:{stream_type}]{trim_type}=start={a}:end={b},{setpts_type}=PTS-STARTPTS[s{i}];"
        streams="".join(["[s%s]"%(i) for i in range(len(timestamps))]) 
        if(stream_type=="v"):
          build_concats+=f"{streams}concat=v=1:a=0[out];"
        elif(stream_type=="a"):
          build_concats+=f"{streams}concat=v=0:a=1[out];"

        #remove the last semicolon.
        build_concats=build_concats[:-1]

        #generate the filenames
        if stream_type=="v":
            new_filename=get_filename(os.path.basename(input_file),timestamps,"mp4")
        elif stream_type=="a":
            new_filename=get_filename(os.path.basename(input_file),timestamps,"wav")
        else:
            new_filename=get_filename(os.path.basename(input_file),timestamps)

        output_file=os.path.join(output_folder,new_filename)

        build_concats+=f'" -map [out] '+f'"{output_file}"'
        if Execute:
            with open(logs_path,"a") as logs:
                subp.check_call(
                build_concats,stdout=logs,
                stderr=logs,shell=True)
    else:
        if depth_list>1 and len(timestamps)==1:
            a,b=timestamps[0]
        else:
            a,b = timestamps
        build_concats=f'ffmpeg -threads {threads} -y -i "{input_file}" -filter_complex "'
        build_concats+=f"[0:{stream_type}]{trim_type}=start={a}:end={b},{setpts_type}=PTS-STARTPTS[s0];"

        #remove the last semicolon.
        build_concats=build_concats[:-1]

        if stream_type=="v":
            new_filename=get_filename(os.path.basename(input_file),timestamps,"mp4")
        elif stream_type=="a":
            new_filename=get_filename(os.path.basename(input_file),timestamps,"wav")
        else:
            new_filename=get_filename(os.path.basename(input_file),timestamps)

        output_file=os.path.join(output_folder,new_filename)
       
        build_concats+=f'" -map [s0] '+f'"{output_file}"'
        if Execute:
           with open(logs_path,"a") as logs:
            subp.check_call(
            build_concats,stdout=logs,
            stderr=logs,shell=True)


    return new_filename
        
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
