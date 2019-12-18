class MLModel(object):
    def __init__(self, name):
        self.name = name
        pass

    def train_ml_model(self, train_data):
        raise NotImplementedError

    def evaluate_ml_model(self, test_data):
        raise NotImplementedError

    def predict_ml_model(self, x_new):
        raise NotImplementedError
