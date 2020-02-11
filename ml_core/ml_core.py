import pickle
from ml_core.ml_ANN import ANN
from ml_core.ml_classifier import Classifier
from utilities import file_management as fm
import os

class MLCore:
    def __init__(self):
        '''
        Constructor
        :param mdl: the name of the model (string)
        '''
        self.available_models = ("ANN", "Classifier")
        self.models = {name : None for name in self.available_models}
        self.is_model_trained = {name : False for name in self.available_models}
        self.video_df = None
        self.audio_df = None
        self.meta_df = None
        self.model_path = None

    def set_audio_dataframe(self, a_df):
        self.audio_df = a_df

    def set_video_dataframe(self, v_df):
        self.video_df = v_df

    def set_metadata_dataframe(self, m_df):
        self.meta_df = m_df

    def create_models(self, model_path):
        self.model_path = model_path
        for model_name in self.available_models:
            self.create_model(model_name)
            self._train_model(model_name)

    def create_model(self, model_name):
        stored_models = fm.getfiledictionary(path=self.model_path)

        # if model exist, load it
        if model_name in stored_models.keys():
            self.models[model_name] = pickle.load(open(stored_models[model_name], "rb"))
            self.is_model_trained[model_name] = True
            return

        if model_name == "ANN":
                _, insize = self.video_df.shape
                _, outsize = self.audio_df.shape
                self.models[model_name] = ANN(model_name, batch_size=64, epochs=100,
                                              input_size=insize, output_size=outsize-1)
        elif model_name == "Classifier":
                self.models[model_name] = Classifier(model_name)

        self.is_model_trained[model_name] = False

    def _train_model(self, model_name):
        """
        Method to train core machine learning model
        :param model_name: Model to train
        :return:
        """
        if self.is_model_trained[model_name]:
            return

        self.models[model_name].train_ml_model(self.video_df, self.audio_df, self.meta_df)
        self._save_model(model_name)
        self.is_model_trained[model_name] = True

    def evaluate_model(self):
        """
        Method to evaluate core machine learning model
        :param test_data: Dataframe containing test data
        :return: Metrics
        """
        loss = self.models["ANN"].evaluate_ml_model(self.video_df, self.audio_df, self.meta_df)
        return loss

    def predict(self, new_video_ftrs):
        """
        Method to suggest a music score for a video
        :param new_video_ftrs: Features of the video
        :return: Dictionary containing predictions of the models
        """
        predictions = {}
        for index, model_name in enumerate(self.available_models):
            predictions[index] = self.models[model_name].predict_ml_model(self.video_df,
                                                                          self.audio_df,
                                                                          self.meta_df,
                                                                          new_video_ftrs)
        return predictions

    def get_model_name_from_index(self,idx):
        return self.available_models[idx]

    def _save_model(self, model_name):
        """
        Method to save trained model
        :param model_name: Name of the file to save model to
        :return:
        """
        pickle.dump(self.models[model_name], open(os.path.join(self.model_path, model_name), "wb"))

