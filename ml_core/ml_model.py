class MLModel(object):
    def __init__(self, name):
        self.name = name
        pass

    def get_name(self):
        '''
        Method to return the name of the model
        :return: the name of the model
        '''
        return self.name

    def train_ml_model(self, vdata, adata, mdata):
        raise NotImplementedError

    def evaluate_ml_model(self, vdata, adata, mdata):
        raise NotImplementedError

    def predict_ml_model(self, vdata, adata, mdata, video_new, video_new_path):
        raise NotImplementedError

    def save_model(self, destination):
        """
        Method to save model
        Args:
            destination: Destination directory
        """
        raise NotImplementedError

    def load_model(self, source):
        """
        Method to load saved model
        Args:
            source: Source directory
        """
        raise NotImplementedError
