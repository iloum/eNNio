import pickle
from ml_core.ml_ANN import ANN
from utilities import file_management as fm


class MLCore:
    def __init__(self):
        '''
        Constructor
        :param mdl: the name of the model (string)
        '''
        self.name = None
        self.modelclass = None
        self.video_df = None
        self.audio_df = None
        self.meta_df = None

        pass

    def set_audio_dataframe(self, a_df):
        self.audio_df = a_df

    def set_video_dataframe(self, v_df):
        self.video_df = v_df

    def set_metadata_dataframe(self, m_df):
        self.meta_df = m_df

    def create_model(self, model_name, model_path):
        self.name = model_name
        stored_models = fm.getfiledictionary(path=model_path)
        if model_name == "ANN":
            if model_name in stored_models.keys():  # if model exist, load it
                self.modelclass = pickle.load(open(stored_models[model_name], "rb"))
            else:  # else create it
                _, insize = self.video_df.shape
                _, outsize = self.audio_df.shape
                self.modelclass = ANN("ANN", batch_size=64, epochs=100, input_size=insize, output_size=outsize)

    def train_model(self):
        """
        Method to train core machine learning model
        :param train_data: Dataframe containing training data
        :return:
        """

        self.modelclass.train_ml_model(self.video_df, self.audio_df, self.meta_df)
        return True

    def evaluate_model(self):
        """
        Method to evaluate core machine learning model
        :param test_data: Dataframe containing test data
        :return: Metrics
        """
        loss = self.modelclass.evaluate_ml_model(self.video_df, self.audio_df, self.meta_df)
        return loss

    def predict(self, new_video_ftrs):
        """
        Method to suggest a music score for a video
        :param video_features: Features of the video
        :return: Music score id
        """
        y_predict = self.modelclass.predict_ml_model(self.video_df, self.audio_df, self.meta_df, new_video_ftrs)
        return y_predict

    def save_ml_core(self):
        """
        Method to save trained model
        :param filename: Name of the file to save model to
        :return:
        """
        pickle.dump(self.modelclass, open(self.name, "wb"))
        return True


