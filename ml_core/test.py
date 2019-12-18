import pandas as pd
from ml_core.ml_ANN import ANN
from ml_core.adv_ml_core import MLCore


dataframe = pd.read_csv("D:\\test\\housing.csv", delim_whitespace=True, header=None)
dataset = dataframe.values
# split into input (X) and output (Y) variables
X = dataset[:, 0:12]
Y = dataset[:, 12:13]

ann_mdl_cls = ANN("ANN", batch_size=64, epochs=15, inputsize= X.shape[1], outputsize= Y.shape[1])


mlCORE = MLCore(ann_mdl_cls)

mlCORE.train_model(dataset)
mlCORE.save_ml_core("D:\\test\\mdl.p")

y_pr = mlCORE.predict(dataset[2:3, 0:12])

print(y_pr)
