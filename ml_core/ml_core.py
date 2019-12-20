import pickle
from ml_core.ml_ANN import ANN
from utilities import file_management as fm

class MLCore:
    def __init__(self, mdl):
        '''
        Constructor
        :param mdl: the name of the model (string)
        '''
        self.name = mdl
        storedmodels = fm.getfiledictionary(path="D:\\Test\\models")  # to be changed
        if mdl == "ANN":
            if mdl in storedmodels.keys():  # if model exist, load it
                self.modelclass = pickle.load(open(storedmodels[mdl], "rb"))
            else:  # else create it
                self.modelclass = ANN("ANN", batch_size=64, epochs=15, inputsize=554, outputsize=10)
        pass

    def train_model(self, train_data):
        """
        Method to train core machine learning model
        :param train_data: Dataframe containing training data
        :return:
        """

        self.modelclass.train_ml_model(train_data)
        return True

    def evaluate_model(self, test_data):
        """
        Method to evaluate core machine learning model
        :param test_data: Dataframe containing test data
        :return: Metrics
        """
        loss, accuracy = self.modelclass.evaluate_ml_model(test_data)
        return loss, accuracy

    def predict(self, video_features):
        """
        Method to suggest a music score for a video
        :param video_features: Features of the video
        :return: Music score id
        """
        y_predict = self.modelclass.predict_ml_model(video_features)
        return y_predict

    def save_ml_core(self):
        """
        Method to save trained model
        :param filename: Name of the file to save model to
        :return:
        """
        pickle.dump(self.modelclass, open(self.name, "wb"))
        return True
