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

    def predict_ml_model(self, vdata, adata, mdata, video_new):
        raise NotImplementedError
