import os
from pyAudioAnalysis.MidTermFeatures import mid_feature_extraction, beat_extraction
from pyAudioAnalysis import audioBasicIO
import numpy as np


class AudioFeatureExtractor:
    def __init__(self):
        pass

    def extract_audio_features(self,
                               file_path,
                               mid_window=1,
                               mid_step=1,
                               short_window=0.05,
                               short_step=0.05,):
        """
        Method to extract audio features from an audio file
        :param file_path: Name of the audio file
        :param mid_window: the mid-term window in seconds
        :param mid_step: the mid-term step
        :param short_window: the short-term window
        :param short_step: the short-term step
        :return: Numpy array containing audio features, list of mid-feature names
        """
        # check for empty file
        if os.stat(file_path).st_size == 0:
            print("   (EMPTY FILE -- SKIPPING)")
            # read sampling rate
        [sampling_rate, signal] = audioBasicIO.read_audio_file(file_path)

        mid_features, short_features, mid_feature_names = \
            mid_feature_extraction(signal, sampling_rate,
                                   round(mid_window * sampling_rate),
                                   round(mid_step * sampling_rate),
                                   round(sampling_rate * short_window),
                                   round(sampling_rate * short_step))
        beat, beat_conf = beat_extraction(short_features, short_step)
        mid_features = np.transpose(mid_features)
        # long term averaging of mid-term statistics
        mid_features = mid_features.mean(axis=0)
        if (not np.isnan(mid_features).any()) and \
                (not np.isinf(mid_features).any()):
            mid_features = np.append(mid_features, beat)
            mid_features = np.append(mid_features, beat_conf)
        return mid_features

