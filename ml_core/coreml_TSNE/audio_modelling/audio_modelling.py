from .audio_feature_extractor import AudioFeatureExtractor
import os

import re
import pickle


### emotion/ shot captioning
from pathlib import Path


def update_items(path,save_path):
    print("processing audio...")
    audio_dict = {}
    aufe = AudioFeatureExtractor()
    try:
        if os.path.isdir(path):
            for file_path in Path(path).glob('*.wav'):
                print(file_path)
                try:
                    audio_dict[str(file_path)]=aufe.extract_audio_features(file_path,1,1,.1,.1)
                except:
                    pass
        elif os.path.isfile(path):
            print(path)
            try:
                audio_dict[str(file_path)]=aufe.extract_audio_features(file_path,1,1,.1,.1)
            except:
                pass
        else:
            print('invalid path..')
    except KeyboardInterrupt:
        pass
    print("persisting audio to disk... ")
    try:
        with open(os.path.join(save_path,'audiofeatures.dict'), 'rb') as handle:
            persisted_audios_dict = pickle.load(handle)
        persisted_audios_dict.update(audio_dict)

        with open(os.path.join(save_path,'audiofeatures.dict'), 'wb') as handle:
            pickle.dump(persisted_audios_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

        return persisted_audios_dict
    except:
        with open(os.path.join(save_path,'audiofeatures.dict'), 'wb') as handle:
            pickle.dump(audio_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

            return audio_dict

def load_file(path):
    if os.path.isfile(path):
        aufe = AudioFeatureExtractor()
        return aufe.extract_audio_features(path,1,1,.1,.1)
    else:
        print("invalid file...")


def load_items(path):
    with open(os.path.join(path,'audiofeatures.dict'), 'rb') as handle:
        persisted_audios_dict = pickle.load(handle)
    return persisted_audios_dict

def drop_items(path):
    os.remove(os.path.join(path,'audiofeatures.dict'))
 
