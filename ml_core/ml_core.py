class MLCore:
    def __init__(self):
        pass

    def train_model(self, train_data):
        """
        Method to train core machine learning model
        :param train_data: Dataframe containing training data
        :return:
        """
        pass

    def evaluate_model(self, test_data):
        """
        Method to evaluate core machine learning model
        :param test_data: Dataframe containing test data
        :return: Metrics
        """
        pass

    def predict(self, video_features):
        """
        Method to suggest a music score for a video
        :param video_features: Features of the video
        :return: Music score id
        """
        pass

    def save_model(self, filename):
        """
        Method to save trained model
        :param filename: Name of the file to save model to
        :return:
        """
        pass