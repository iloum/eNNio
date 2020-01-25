from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.optimizers import SGD, Adam, RMSprop
from ml_core.ml_model import MLModel
from data_preprocessor import data_preprocessor as dp
import tensorflow as tf
from keras import regularizers
from ml_core import mp_utils as mu
from sklearn.neighbors import KNeighborsClassifier
import pickle
import os

class ANN(MLModel):
    def __init__(self, name, batch_size, epochs, v_df, a_df, m_df):
        self._data_dir = self._config_manager.get_field('data-folder')
        self.video_df = v_df
        self.audio_df = a_df
        self.metadata_df = m_df
        self.x_data_scl, self.y_data_scl, \
        self.x_scaler, self.y_scaler = dp.apply_minmax_scaler(self.video_df, self.audio_df)

        self.x_train, self.x_test, \
        self.y_train, self.y_test = mu.custom_train_test_split(self.video_df, self.audio_df,
                                                               self.metadata_df, 0.10,
                                                               self.x_scaler, self.y_scaler,
                                                               random_state=42)

        self.batch_size = batch_size
        self.epochs = epochs
        self.model = Sequential()
        self.input_size, _ = self.x_data_scl.shape
        self.output_size, _ = self.y_data_scl.shape

        self.model = Sequential()
        self.model.add(Dense(200, activation='tanh', input_shape=(self.input_size,)))
        self.model.add(Dense(200, activation='tanh', kernel_regularizer=regularizers.l2(0.0001)))
        self.model.add(Dense(200, activation='tanh', kernel_regularizer=regularizers.l2(0.0001)))
        self.model.add(Dense(100, activation='tanh', kernel_regularizer=regularizers.l2(0.0001)))
        self.model.add(Dense(self.output_size, activation='tanh', kernel_regularizer=regularizers.l2(0.0001)))
        self.model.summary()
        self.model.compile(loss='mean_squared_error', optimizer=Adam())

        super().__init__(name)
        pass




    def get_name(self):
        '''
        Method to return the name of the model
        :return: the name of the model
        '''
        return self.name

    def train_ml_model(self):
        '''
        method to train the model
        :param train_data: the data for training
        :return: the trained model
        '''
        self.model.fit(self.x_data_scl, self.y_data_scl,
                       batch_size=self.batch_size,
                       epochs=self.epochs,
                       verbose=1)

        pickle.dump(self.model, open(os.path.join(self._data_dir, self.name+".pkl"), "wb"))
        return True

    def evaluate_ml_model(self):
        '''
        Method to evaluate the model based on test data
        :param test_data: data used for testing and evaluation
        :return: loss anc accuracy metrics
        '''

        self.model.fit(self.x_train, self.y_train,
                       batch_size=self.batch_size,
                       epochs=self.epochs,
                       verbose=1, validation_data=(self.x_test, self.y_test))

        score = self.model.evaluate(self.x_test, self.y_test, verbose=0)

        loss = score
        return loss

    def predict_ml_model(self, x_new):
        '''
        Method to predict based on input
        :param x_new: new unseen data
        :return: the predited value
        '''
        ann_mdl = pickle.load(open(os.path.join(self._data_dir, self.name+".pkl"), "rb"))

        x_knn = self.y_data_scl
        y_knn = list(self.audio_df.index.values)
        neigh = KNeighborsClassifier(n_neighbors=1, algorithm="brute", p=2)
        neigh.fit(x_knn, y_knn)

        x_new_reshaped = x_new.reshape((1, self.input_size))
        x_new_scaled = self.x_scaler.transform(x_new_reshaped)
        y_pr = ann_mdl.predict(x_new_scaled)

        knn_predict = neigh.predict(y_pr)
        predicted_audio = self.metada_ftrs.loc[knn_predict, "Audio file path"].values

        print("predict:", self.metada_ftrs.loc[knn_predict, "Url"].values)

        return predicted_audio[0]




