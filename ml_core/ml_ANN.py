from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import SGD
from ml_core.ml_model import MLModel
import tensorflow as tf


class ANN(MLModel):
    def __init__(self, name, batch_size, epochs, inputsize, outputsize):
        self.batch_size = batch_size
        self.epochs = epochs
        self.model = Sequential()
        self.model.add(Dense(20, input_shape=(inputsize,), activation='tanh'))
        self.model.add(Dense(10, activation='tanh'))
        self.model.add(Dense(outputsize, activation='tanh'))
        self.model.compile(loss='mean_squared_error', optimizer='adam')
        super().__init__(name)
        pass

    def get_name(self):
        '''
        Method to return the name of the model
        :return: the name of the model
        '''
        return self.name

    def train_ml_model(self, train_data):
        '''
        method to train the model
        :param train_data: the data for training
        :return: the trained model
        '''
        x_data = train_data[:, 0:12]  # to be changed
        y_data = train_data[:, 12:13]  # to be changed

        self.model.compile(loss='mean_squared_error',
                      optimizer=SGD(),
                      metrics=['accuracy'])
        self.model.fit(x_data, y_data,
                        batch_size=self.batch_size,
                        epochs=self.epochs,
                        verbose=1)
        return self.model

    def evaluate_ml_model(self, test_data):
        '''
        Method to evaluate the model based on test data
        :param test_data: data used for testing and evaluation
        :return: loss anc accuracy metrics
        '''
        x_test = test_data[:, 0:12]
        y_test = test_data[:, 0:12]

        score = self.model.evaluate(x_test, y_test, verbose=0)
        loss = score[0]
        accuracy = score[1]
        return loss, accuracy

    def predict_ml_model(self, x_new):
        '''
        Method to predict based on input
        :param x_new: new unseen data
        :return: the predited value
        '''
        y_predict = self.model.predict(x_new)
        return y_predict




