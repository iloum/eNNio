import random
from math import sqrt
import numpy as np
import os
import pickle
from ml_core.mp_utils import my_train_test_split
from ml_core.ml_model import MLModel
from data_preprocessor import data_preprocessor as dp
from sklearn.utils import shuffle
from sklearn.svm import SVC


class Classifier(MLModel):
    def __init__(self, name):
        super(Classifier, self).__init__(name)
        self.model = None
        self._video_normalizer = None
        self._audio_normalizer = None
        self._video_reducer = None
        self._audio_reducer = None
        self._trans_audio_df = None

    @staticmethod
    def _create_not_matching_entries(num_of_entries, metadata):
        mappings = {}
        videos = random.sample(metadata.index.tolist(), num_of_entries)
        for video in videos:
            candidates = metadata[metadata["Url"] == metadata.at[video, "Mismatch URL"]]
            mappings[video] = random.choice(candidates.index)
        return mappings

    def _get_feature_target_arrays(self, video_df, audio_df, metadata_df):
        x_matching = np.hstack((video_df.values, audio_df.values))
        y_matching = np.ones((x_matching.shape[0], 1))
        no_match_mapping = self._create_not_matching_entries(x_matching.shape[0],
                                                             metadata_df)
        x_not_matching = np.hstack((video_df.loc[no_match_mapping.keys()].values,
                                      audio_df.loc[no_match_mapping.values()].values))
        y_not_matching = np.zeros((x_not_matching.shape[0], 1))
        x_train = np.vstack((x_matching, x_not_matching))
        y_train = np.vstack((y_matching, y_not_matching)).ravel()
        return shuffle(x_train, y_train)

    def train_ml_model(self, video_df, audio_df, metadata_df):
        """
        method to train the model
        :param video_df: Dataframe containing video features
        :param audio_df: Dataframe containing audio features
        :param metadata_df: Dataframe containing metadata
        :return: the trained model
        """
        self.model = SVC(C=0.001, gamma=1, kernel='poly', probability=True, random_state=2020)

        norm_video_df, self._video_normalizer = dp.normalize_df(video_df)
        proc_audio_df = dp.remove_beat_conf_column(audio_df)  # remove columns with None
        norm_audio_df, self._audio_normalizer = dp.normalize_df(proc_audio_df)

        trans_video_df, self._video_reducer = dp.reduce_dimensions_svd(norm_video_df,
                                                                       round(sqrt(norm_video_df.shape[0])))
        self._trans_audio_df, self._audio_reducer = dp.reduce_dimensions_svd(norm_audio_df,
                                                                       round(sqrt(norm_audio_df.shape[0])))

        x_train, y_train = self._get_feature_target_arrays(video_df=trans_video_df, audio_df=self._trans_audio_df,
                                                           metadata_df=metadata_df)
        self.model.fit(x_train, y_train)

        return self.model

    def save_model(self, destination):
        """
        Method to save model
        Args:
            destination: Destination directory
        """
        pickle.dump(self.model,
                    open(os.path.join(destination,
                                      self.name + '_model.pkl'), "wb"))
        pickle.dump(self._video_normalizer,
                    open(os.path.join(destination,
                                      self.name + '_vnorm.pkl'), "wb"))
        pickle.dump(self._audio_normalizer,
                    open(os.path.join(destination,
                                      self.name + '_anorm.pkl'), "wb"))
        pickle.dump(self._video_reducer,
                    open(os.path.join(destination,
                                      self.name + '_vreduce.pkl'), "wb"))
        pickle.dump(self._audio_reducer,
                    open(os.path.join(destination,
                                      self.name + '_areduce.pkl'), "wb"))

    def load_model(self, source):
        """
        Method to load saved model
        Args:
            source: Source directory
        """
        self.model = pickle.load(
            open(os.path.join(source, self.name + '_model.pkl'), "rb"))
        self._video_normalizer = pickle.load(
            open(os.path.join(source, self.name + '_vnorm.pkl'), "rb"))
        self._audio_normalizer = pickle.load(
            open(os.path.join(source, self.name + '_anorm.pkl'), "rb"))
        self._video_reducer = pickle.load(
            open(os.path.join(source, self.name + '_vreduce.pkl'), "rb"))
        self._audio_reducer = pickle.load(
            open(os.path.join(source, self.name + '_areduce.pkl'), "rb"))


    def evaluate_ml_model(self, video_df, audio_df, metadata_df):
        """
        Method to evaluate the model based on test data
        :param video_df: Dataframe containing video features
        :param audio_df: Dataframe containing audio features
        :param metadata_df: Dataframe containing metadata
        :return: loss anc accuracy metrics
        """
        pass

    def predict_ml_model(self, video_df, audio_df, metadata_df, video_new, video_new_path=None):
        """
        Method to predict based on input
        :param video_df: Dataframe containing video features
        :param audio_df: Dataframe containing audio features
        :param metadata_df: Dataframe containing metadata
        :param video_new: new unseen data
        :param video_new_path: Unused here
        :return: the predited value
        """

        norm_video_new = self._video_normalizer.transform(video_new.values)

        trans_video_new = self._video_reducer.transform(norm_video_new)

        suggestions = []
        proc_audio_df = dp.remove_beat_conf_column(audio_df)  # remove columns with None

        for index, audio in proc_audio_df.iterrows():
            norm_audio_new = self._audio_normalizer.transform(
                audio.values.reshape(1, len(audio)))

            trans_audio_new = self._audio_reducer.transform(norm_audio_new)
            x = np.hstack((trans_video_new, trans_audio_new))

            probs = self.model.predict_proba(x).ravel().tolist()
            max_prob = max(probs)
            if probs.index(max_prob) == 1:
                suggestions.append((index, max_prob))

        return sorted(suggestions, key=lambda t: t[1])[0][0]




