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
from .utils.utils import *




def main(args):

    downloads_folder=os.path.join(args.outputfolder,"downloaded")
    parsed_folder=os.path.join(args.outputfolder,"parsed")

    create_folder(args.outputfolder)
    create_folder(downloads_folder)
    create_folder(parsed_folder)
    create_folder(os.path.join(downloads_folder,"audio"))
    create_folder(os.path.join(downloads_folder,"video"))
    create_folder(os.path.join(parsed_folder,"audio"))
    create_folder(os.path.join(parsed_folder,"video"))
    
    
    persisted_meta_f=os.path.join(args.outputfolder,".youtubelinks_meta")
    if os.path.exists(persisted_meta_f):
        with open(persisted_meta_f) as f:
            persisted_meta=json.loads(f.read())
    else:
        print("creating a metadata file")
        persisted_meta={}
    
    default_specs={"res":144,"fps":30,"abr":50}


    with open(args.filename) as csv_file:
        inputs=csv_file.readlines()

    badinputs=[]

    with open(args.filename) as csv_file:
        csv_data = list(csv.DictReader(csv_file, delimiter='|'))

    onego_metalist=[]
    for indexi,rawitem in enumerate(csv_data):
        print("\n\n")
        print("*** processing link ", rawitem['link']," ***")
        #flags to compare specs
        skip_download=False
        skip_parsing=False
        new_entry=False


        parsed_item={}
        parsed_item['link']=rawitem['link']
        parsed_item['specs']={}
        #parsed_item['comment']=rawitem["comment"]

        if rawitem.get('res') or rawitem.get('fps') or rawitem.get('abr'):
        #if at least one is provided then update the rest with dummies
            for spec in ['res','fps','abr']:
                if rawitem.get(spec):
                    parsed_item['specs'][spec]=rawitem[spec]
                else:
                    parsed_item['specs'][spec]=99999
        else:
        #if all are missing then defaults
            parsed_item['specs']=default_specs

        if rawitem.get('timestamps'):
            parsed_item['timestamps']=eval(timestamp_input_parser(rawitem['timestamps']))
            parsed_item['timestamps']=convert_timestamps(parsed_item['timestamps'])
            parsed_item['timestamps'].sort()
        else:
            parsed_item['timestamps']=["nocuts"]
        

        #checks if current parsed_item is in previously downloaded rawitems
        if persisted_meta and (parsed_item['link'] in persisted_meta.keys()):
            
            persisted_item = persisted_meta[parsed_item['link']]
           
            if compareflat_dict(parsed_item['specs'],persisted_item['specs']) and persisted_item['filenames']:
                skip_download=True
                
                if compare_lists(parsed_item["timestamps"],persisted_item['timestamps']):
                    skip_parsing=True
                else:
                    skip_parsing=False

            else:
                skip_download=False
                skip_parsing=False

        else:
            new_entry=True
            skip_download=False
            skip_parsing=False


        if new_entry:
                persisted_meta[parsed_item['link']]={
                "link":parsed_item['link'],
                'specs':parsed_item['specs'],
                'filenames':[],
                'timestamps':[]
                #'comments':parsed_item['comment']
                } 

        if skip_download or skip_parsing:
            print("found an item registered using the same link")
        try:
            if skip_download:
                print("checking consistency of downloaded files..")
                print("checking downloaded files...")
                filename_audio=persisted_item['filenames']['downloaded_audio']
                filename_video=persisted_item['filenames']['downloaded_video']
                if os.path.exists(filename_video):
                    print("video is matching...")
                else:
                    print("video appears to be missing, downloading video...")
                    filename_video=download_ytbvideo(parsed_item['link'],"v",downloads_folder,parsed_item['specs'])
                    print("downloaded ", filename_video)

                if os.path.exists(filename_audio):
                    print("audio is matching...")
                else:
                    print("audio appears to be missing, downloading audio...")
                    filename_audio=download_ytbvideo(parsed_item['link'],"a",downloads_folder,parsed_item['specs'])
                    print("downloaded ", filename_audio)
            else:
                print("downloading video...")
                filename_video=download_ytbvideo(parsed_item['link'],"v",downloads_folder,parsed_item['specs'])
                print("downloaded ", filename_video)
                print("downloading audio...")
                filename_audio=download_ytbvideo(parsed_item['link'],"a",downloads_folder,parsed_item['specs'])
                print("downloaded ", filename_audio)


            timestamps=parsed_item['timestamps']
            if skip_parsing:
                print("checking consistency of parsed files")
                
                print("checking video files...")
                parsed_video_filenames=cropper(filename_video,"video",timestamps,[parsed_folder,"video"],args.threads)
                
                print("checking audio files...")
                parsed_audio_filenames=cropper(filename_audio,"audio",timestamps,[parsed_folder,"audio"],args.threads)
                 
            else:
                parsed_video_filenames=cropper(filename_video,"video",timestamps,[parsed_folder,"video"],args.threads)
                parsed_audio_filenames=cropper(filename_audio,"audio",timestamps,[parsed_folder,"audio"],args.threads)
            

            parsed_item['filenames']={"downloaded_audio":filename_audio,"downloaded_video":filename_video,
            "parsed_video":parsed_video_filenames,"parsed_audio":parsed_audio_filenames}
            

            if new_entry:
                persisted_meta[parsed_item['link']]={
                "link":parsed_item['link'],
                'specs':parsed_item['specs'],
                'filenames':parsed_item['filenames'],
                'timestamps':[parsed_item['timestamps']]
                #'comments':parsed_item['comment']
                } 
            else:
                
                persisted_meta[parsed_item['link']]['filenames']['downloaded_video']=filename_video
                persisted_meta[parsed_item['link']]['filenames']['downloaded_audio']=filename_audio

                timestamps_found=[compare_lists(parsed_item['timestamps'], item) for item in persisted_meta[parsed_item['link']]['timestamps']]
                print(timestamps_found)
                print(parsed_item['timestamps'])
                print(persisted_meta[parsed_item['link']]['timestamps'])
                if any(timestamps_found):
                    pass
                else:
                    persisted_meta[parsed_item['link']]['timestamps'].append(parsed_item['timestamps'])

                if parsed_video_filenames not in persisted_meta[parsed_item['link']]['filenames']['parsed_video']:
                    persisted_meta[parsed_item['link']]['filenames']['parsed_video'].extend(parsed_video_filenames)
                if parsed_audio_filenames not in persisted_meta[parsed_item['link']]['filenames']['parsed_audio']:
                    persisted_meta[parsed_item['link']]['filenames']['parsed_audio'].extend(parsed_audio_filenames)

                #persisted_meta[parsed_item['link']]['filenames']['comments'].extend(parsed_item["comment"])
        
            onego_metalist.append(persisted_meta[parsed_item['link']])
        
        except KeyboardInterrupt:
            with open(persisted_meta_f,'w') as f:
                writer=f.write(json.dumps(persisted_meta))
            break
        except Exception as e:
            if not badinputs:
                #setup bad inputs file
                badinputsloc=os.path.join(args.outputfolder,"badinputs.csv")
                remove_file(badinputsloc)
                
                headers=inputs[0]
                with open(badinputsloc,"w") as bad_inputsf:
                    #write headers to badfile inputs
                    bad_inputsf.write(headers)
                
            badinput=inputs[indexi+1]
            with open(badinputsloc,"a") as bad_inputsf:
                bad_inputsf.write(badinput)

            badinputs.append((indexi,badinput.split("|")[0],str(e)))

        with open(persisted_meta_f,'w') as f:
            writer=f.write(json.dumps(persisted_meta))

    if badinputs:
        print("\n"*3)
        error_reportmsg="ERROR REPORT:"
        print("-"*len(error_reportmsg))
        print(error_reportmsg)
        print("-"*len(error_reportmsg))
        print(" I was not able to work on the following inputs ")
        for indexi,badinput,error in badinputs:
            print("\n"*2)
            print("input"+str(indexi)+":"+badinput)
            print(error)

        badinputslog=os.path.join(args.outputfolder,"badinputs.log")
        remove_file(badinputslog)
        with open(badinputslog,"a") as f:
            for indexi,badinput,error in badinputs:
                f.write("\n"*2)
                f.write("input"+str(indexi)+":"+badinput)
                f.write(error)

    return persisted_meta,onego_metalist


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = 'Welcome to Bifröst wanderer. To cross, you have to sacrifice youtube videos.')
    parser.add_argument('-f',"--filename",type=str,help="provide a csv file to read the youtube links, cropping timestamps and the download specs [optional] for the video")
    parser.add_argument('-o',"--outputfolder",type=str,help="path were files will be stored")
    parser.add_argument('-t',"--threads",type=int,help="number of threads to be used during cropping",default=2)

    args = parser.parse_args()

    main(args)
