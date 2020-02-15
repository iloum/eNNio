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

from .Emotion_detection import detect as ev


def update_items(path,save_path):

    print("captioning videos...")
    try:
        emotions_dict=ev.generate_emotionfeatures(path)
    except KeyboardInterrupt:
        pass

    print("persisting captions to disk... ")
    try:
        with open(os.path.join(save_path,'emotionfeatures.dict'), 'rb') as handle:
            persisted_emotions_dict = pickle.load(handle)
        persisted_emotions_dict.update(emotions_dict)

        with open(os.path.join(save_path,'emotionfeatures.dict'), 'wb') as handle:
            pickle.dump(persisted_emotions_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

        return persisted_emotions_dict
    except:
        with open(os.path.join(save_path,'emotionfeatures.dict'), 'wb') as handle:
            pickle.dump(emotions_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

            return emotions_dict

def load_file(path):
    if os.path.isfile(path):
        return ev.generate_emotionfeatures(path)
    else:
        print("invalid file...")


def load_items(path):
    with open(os.path.join(path,'emotionfeatures.dict'), 'rb') as handle:
        persisted_emotions_dict = pickle.load(handle)
    return persisted_emotions_dict

def drop_items(path):
    os.remove(os.path.join(path,'emotionfeatures.dict'))
