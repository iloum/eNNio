class MLModel(object):
    def __init__(self, name):
        self.name = name
        pass

    def train_ml_model(self, vdata, adata, mdata):
        raise NotImplementedError

    def evaluate_ml_model(self, vdata, adata, mdata):
        raise NotImplementedError

    def predict_ml_model(self, vdata, adata, mdata, video_new):
        raise NotImplementedError
