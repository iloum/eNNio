import pickle
from ml_core.ml_ANN import ANN
from ml_core.ml_classifier import Classifier
from ml_core.ml_TSNE import TSNE
from utilities import file_management as fm
import time
import os

class MLCore:
    def __init__(self):
        '''
        Constructor
        :param mdl: the name of the model (string)
        '''
        self.available_models = ("ANN", "Classifier","TSNE")
        # self.available_models = ("Classifier",)
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
        # If model exists do not overwrite it
        if self.models[model_name]:
            return

        if model_name == "ANN":
            self.models[model_name] = ANN(model_name, batch_size=64, epochs=100)
        elif model_name == "Classifier":
            self.models[model_name] = Classifier(model_name)
        elif model_name == "TSNE":
            self.models[model_name] = TSNE(model_name)

        # if model exist, load it
        if model_name in os.listdir(self.model_path):
            self.models[model_name].load_model(os.path.join(self.model_path,
                                                            model_name))
            print("Loaded model {}".format(model_name))
            self.is_model_trained[model_name] = True
        else:
            self.is_model_trained[model_name] = False

    def _train_model(self, model_name):
        """
        Method to train core machine learning model
        :param model_name: Model to train
        :return:
        """
        if self.is_model_trained[model_name]:
            return

        if model_name == 'TSNE':
            os.makedirs(os.path.join(self.model_path, model_name), exist_ok=True)
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

    def predict(self, new_video_ftrs, new_video_path):
        """
        Method to suggest a music score for a video
        :param new_video_ftrs: Features of the video
        :param new_video_path: Path to video file
        :return: Dictionary containing predictions of the models
        """
        predictions = {}
        for index, model_name in enumerate(self.available_models):
            start_time = time.time()
            predictions[index] = self.predict_using_model(new_video_ftrs, new_video_path, index)
            print("Model {} took {} seconds".format(model_name, time.time() - start_time))
        return predictions

    def predict_using_model(self, new_video_ftrs, new_video_path, model_idx):
        """
        Method to suggest a music score for a video
        :param new_video_ftrs: Features of the video
        :param new_video_path: Path to video file
        :param model_idx: The index model
        :return: Dictionary containing predictions of the models
        """
        model_name = self.available_models[model_idx]
        return self.models[model_name].predict_ml_model(self.video_df,
                                                        self.audio_df,
                                                        self.meta_df,
                                                        new_video_ftrs,
                                                        new_video_path)

    def get_model_name_from_index(self,idx):
        return self.available_models[idx]

    def _save_model(self, model_name):
        """
        Method to save trained model
        :param model_name: Name of the file to save model to
        :return:
        """
        save_dir = os.path.join(self.model_path, model_name)
        os.makedirs(save_dir, exist_ok=True)
        self.models[model_name].save_model(save_dir)
