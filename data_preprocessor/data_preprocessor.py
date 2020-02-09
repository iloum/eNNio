from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import pandas as pd
import pickle
from sklearn.preprocessing import MinMaxScaler

class DataPreprocessor:
    def __init__(self):
        pass

    def preprocess(self, input_data):
        """
        Method to preprocess data
        :param input_data: Dataframe
        :return: Preprocessed Dataframe
        """
        pass


def remove_beat_conf_column(audio_ftrs_df):
    audio_ftrs_proc = audio_ftrs_df.drop(['beat_conf'], axis=1)  # there are NaN in this column
    return audio_ftrs_proc


def read_data_from_pkl(video_path, audio_path, medatada_path):
    video_ftrs = pickle.load(open(video_path, "rb"))
    audio_ftrs = pickle.load(open(audio_path, "rb"))
    metada_ftrs = pickle.load(open(medatada_path, "rb"))
    audio_ftrs_proc = audio_ftrs.drop(['beat_conf'], axis=1)  # there are NaN in this column
    return video_ftrs, audio_ftrs_proc, metada_ftrs

def apply_minmax_scaler(v_ftrs, a_ftrs):
    video_data = v_ftrs.values
    audio_data = a_ftrs.values
    video_scaler = MinMaxScaler(feature_range=(-1, 1))
    audio_scaler = MinMaxScaler(feature_range=(-1, 1))
    video_scaler.fit(video_data)
    audio_scaler.fit(audio_data)
    video_data_scld = video_scaler.transform(video_data)
    audio_data_scld = audio_scaler.transform(audio_data)
    return video_data_scld, audio_data_scld, video_scaler, audio_scaler

def reduce_dimensions(data, newdimension):
    """
    Method to reduce the size of the data
    :param data: the data to be reduced
    :param newdimension: the new size of the data
    :return: the reduced data, the scaler used and the pca
    """
    scaler = StandardScaler()
    scaler.fit(data)
    scaleddata = scaler.transform(data)

    pca = PCA(n_components=newdimension)
    pca.fit(scaleddata)
    newdata = pca.transform(scaleddata)
    return newdata, scaler, pca
