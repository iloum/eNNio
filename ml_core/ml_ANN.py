from tensorflow.keras.models import Sequential, model_from_json
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import SGD, Adam, RMSprop
from ml_core.ml_model import MLModel
from data_preprocessor import data_preprocessor as dp
import tensorflow as tf
from tensorflow.keras import regularizers
from ml_core import mp_utils as mu
from sklearn.neighbors import KNeighborsClassifier
import pickle
import os


class ANN(MLModel):
    def __init__(self, name, batch_size, epochs):
        super().__init__(name)

        os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
        os.environ["CUDA_VISIBLE_DEVICES"] = ""

        self.batch_size = batch_size
        self.epochs = epochs
        self.model = None

    def train_ml_model(self, video_df, audio_df, m_df):
        '''
        method to train the model
        :param train_data: the data for training
        :return: the trained model
        '''
        proc_audio_df = dp.remove_beat_conf_column(audio_df)  # remove columns with None
        insize = video_df.shape[1]
        outsize = proc_audio_df.shape[1]

        self.model = Sequential()
        self.model.add(Dense(200, activation='tanh',
                             input_shape=(insize,)))
        self.model.add(Dense(200, activation='tanh',
                             kernel_regularizer=regularizers.l2(0.0001)))
        self.model.add(Dense(200, activation='tanh',
                             kernel_regularizer=regularizers.l2(0.0001)))
        self.model.add(Dense(100, activation='tanh',
                             kernel_regularizer=regularizers.l2(0.0001)))
        self.model.add(Dense(outsize, activation='tanh',
                             kernel_regularizer=regularizers.l2(0.0001)))
        self.model.summary()
        self.model.compile(loss='mean_squared_error', optimizer=Adam())

        video_data_scl, audio_data_scl, _, _ = dp.apply_minmax_scaler(video_df,proc_audio_df)

        self.model.fit(video_data_scl, audio_data_scl,
                       batch_size=self.batch_size,
                       epochs=self.epochs,
                       verbose=1)

        return self.model

    def save_model(self, destination):
        """
        Method to save model
        Args:
            destination: Destination directory
        """
        model_json = self.model.to_json()
        with open(os.path.join(destination, self.name + ".json"), "w") as json:
            json.write(model_json)
        self.model.save_weights(os.path.join(destination, self.name +
                                             "_weights.h5"))

    def load_model(self, source):
        """
        Method to load saved model
        Args:
            source: Source directory
        """
        json_file = open(os.path.join(source, self.name + ".json"), 'r')
        loaded_model_json = json_file.read()
        json_file.close()
        self.model = model_from_json(loaded_model_json)
        self.model.load_weights(os.path.join(source, self.name +
                                             "_weights.h5"))

    def evaluate_ml_model(self, video_df, audio_df, metadata_df):
        '''
        Method to evaluate the model based on test data
        :param test_data: data used for testing and evaluation
        :return: loss anc accuracy metrics
        '''

        proc_audio_df = dp.remove_beat_conf_column(audio_df)  # remove columns with None
        _, _, video_scaler, audio_scaler = dp.apply_minmax_scaler(video_df, proc_audio_df)

        video_train, video_test, audio_train, audio_test = mu.custom_train_test_split(video_df, proc_audio_df,
                                                               metadata_df, 0.10,
                                                               video_scaler, audio_scaler,
                                                               random_state=42)

        self.model.fit(video_train, audio_train,
                       batch_size=self.batch_size,
                       epochs=self.epochs,
                       verbose=1, validation_data=(video_test, audio_test))

        score = self.model.evaluate(video_test, audio_test, verbose=0)

        loss = score
        return loss

    def predict_ml_model(self, video_df, audio_df, metadata_df, video_new, video_new_path=None):
        '''
        Method to predict based on input
        :param video_df: Dataframe containing video features
        :param audio_df: Dataframe containing audio features
        :param metadata_df: Dataframe containing metadata
        :param video_new: new unseen data
        :param video_new_path: Unused here
        :return: the predited value
        '''
        #ann_mdl = pickle.load(open(os.path.join(self._data_dir, self.name+".pkl"), "rb"))

        proc_audio_df = dp.remove_beat_conf_column(audio_df) # remove columns with None
        _, audio_data_scl, video_scaler, audio_scaler = dp.apply_minmax_scaler(video_df, proc_audio_df)

        x_knn = audio_data_scl
        y_knn = list(proc_audio_df.index.values)
        neigh = KNeighborsClassifier(n_neighbors=1, algorithm="brute", p=2)
        neigh.fit(x_knn, y_knn)

        video_new_nparray = video_new.values  #video_new.reshape((1, self.input_size))
        video_new_scaled = video_scaler.transform(video_new_nparray)
        ann_prediction = self.model.predict(video_new_scaled)

        knn_predict = neigh.predict(ann_prediction)
        #predicted_audio = metadata_df.loc[knn_predict, "Audio file path"].values

        #print("predict:", metadata_df.loc[knn_predict, "Url"].values)

        return knn_predict.tolist()[-1]
