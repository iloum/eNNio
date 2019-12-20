import  pickle

class MLCore:
    def __init__(self, modelcls):
        self.modelclass = modelcls  # the class of the model
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

    def save_ml_core(self,filename):
        """
        Method to save trained model
        :param filename: Name of the file to save model to
        :return:
        """
        pickle.dump(self, open(filename, "wb"))
        return True
