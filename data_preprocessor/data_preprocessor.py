from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

class DataPreprocessor:
    def __init__(self):
        pass

    def preprocess(self, input_data):
        """
        Method to preprocess data
        :param input_data: Dataframe
        :return: Preprocessed Dataframe
        """
        pass


def reduce_dimensions(data, newdimension):
    """
    Method to reduce the size of the data
    :param data: the data to be reduced
    :param newdimension: the new size of the data
    :return: the reduced data, the scaler used and the pca
    """
    scaler = StandardScaler()
    scaler.fit(data)
    scaleddata = scaler.transform(data)

    pca = PCA(n_components=newdimension)
    pca.fit(scaleddata)
    newdata = pca.transform(scaleddata)
    return newdata, scaler, pca
