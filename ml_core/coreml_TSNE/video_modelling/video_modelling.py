import re
import pickle


### emotion/ shot captioning
from pathlib import Path

### visualizations
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import random


import os

from .shot_and_caption import shot_and_videofeatures as sv


def update_items(path,save_path):

    print("captioning videos...")
    caption_dict={}
    try:
        if os.path.isdir(path):
            for file_path in Path(path).glob('*.mp4'):
                print(file_path)
                try:
                    caption_dict[str(file_path)]=sv.generate_videofeatures(file_path)
                except:
                    pass
        elif os.path.isfile(path):
            print(path)
            try:
                caption_dict[str(file_path)]=sv.generate_videofeatures(path)
            except:
                pass
        else:
            print('invalid path..')
    except KeyboardInterrupt:
        pass
    print("persisting captions to disk... ")
    try:
        with open(os.path.join(save_path,'videofeatures.dict'), 'rb') as handle:
            persisted_captions_dict = pickle.load(handle)
        persisted_captions_dict.update(caption_dict)

        with open(os.path.join(save_path,'videofeatures.dict'), 'wb') as handle:
            pickle.dump(persisted_captions_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

        return persisted_captions_dict
    except:
        with open(os.path.join(save_path,'videofeatures.dict'), 'wb') as handle:
            pickle.dump(caption_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

            return caption_dict

def load_file(path):
    if os.path.isfile(path):
        return sv.generate_videofeatures(path)
    else:
        print("invalid file...")


def load_items(path):
    with open(os.path.join(path,'videofeatures.dict'), 'rb') as handle:
        persisted_captions_dict = pickle.load(handle)
    return persisted_captions_dict

def drop_items(path):
    os.remove(os.path.join(path,'videofeatures.dict'))
