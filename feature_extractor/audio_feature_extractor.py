
from pyAudioAnalysis.MidTermFeatures import directory_feature_extraction as dW


class AudioFeatureExtractor:
    def __init__(self):
        pass

    def extract_audio_features(self, folder_name):
        """
        Method to extract audio features from an audio file
        :param folder_name: Name of the folder with the audio files
        :return: Numpy array containing audio features
        """
        # get features from folders (all classes):
        f1, _, fn1 = dW(folder_path=folder_name,
                        mid_window=1,
                        mid_step=1,
                        short_window=0.05,
                        short_step=0.05,
                        compute_beat=True)
        return f1

