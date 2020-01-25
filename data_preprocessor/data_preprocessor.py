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


def read_data_from_pkl(video_path, audio_path, medatada_path):
    video_ftrs = pickle.load(open(video_path, "rb"))
    audio_ftrs = pickle.load(open(audio_path, "rb"))
    metada_ftrs = pickle.load(open(medatada_path, "rb"))
    audio_ftrs_proc = audio_ftrs.drop(['beat_conf'], axis=1)  # there are NaN in this column
    return video_ftrs, audio_ftrs_proc, metada_ftrs

def apply_minmax_scaler(v_ftrs, a_ftrs):
    x_data = v_ftrs.values
    y_data = a_ftrs.values
    x_scaler = MinMaxScaler(feature_range=(-1, 1))
    y_scaler = MinMaxScaler(feature_range=(-1, 1))
    x_scaler.fit(x_data)
    y_scaler.fit(y_data)
    x_data_scld = x_scaler.transform(x_data)
    y_data_scld = y_scaler.transform(y_data)
    return x_data_scld, y_data_scld, x_scaler, y_scaler

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
