import pandas as pd

from ml_core.ml_core import MLCore
# sometimes I have to refactor ml_core in order to run
import data_preprocessor.data_preprocessor as preproc
import random

#dataframe = pd.read_csv("D:\\test\\housing.csv", delim_whitespace=True, header=None)
#dataset = dataframe.values
# split into input (X) and output (Y) variables
#X = dataset[:, 0:12]
#Y = dataset[:, 12:13]

# ****PREPROCESSING****
# print(X)
#print(X.shape)
#newX, _, _ = preproc.reduce_dimensions(X, 4)
# print(newX)
#print(newX.shape)

# *******ML CORE***********
video_path="D:\\Programming\\DataScience\\MasterDS\\Multimodal\\SemesterProject\\ennIO\\data\\video_features_df_{ftlist_[lbps,hogs,colors,flow],width_300,step_3}.pkl"
audio_path="D:\\Programming\\DataScience\\MasterDS\\Multimodal\\SemesterProject\\ennIO\\data\\audio_features_df_{mid_window_5,mid_step_0.5,short_window_1,short_step_0.5}.pkl"
medatada_path="D:\\Programming\\DataScience\\MasterDS\\Multimodal\\SemesterProject\\ennIO\\data\\metadata_df.pkl"
video_df, audio_df, meta_df = preproc.read_data_from_pkl(video_path, audio_path, medatada_path)
model_paths = "D:\\Programming\\DataScience\\MasterDS\\Multimodal\\SemesterProject\\ennIO\\data"

#ann_mdl_cls = ANN("ANN", batch_size=64, epochs=15, video_df, audio_df, meta_df)
mlCORE = MLCore()
mlCORE.set_audio_dataframe(audio_df)
mlCORE.set_video_dataframe(video_df)
mlCORE.set_metadata_dataframe(meta_df)

annml = mlCORE.create_model("ANN", model_paths)
annml._train_model()
annml.save_ml_core()
vindex_lst = list(video_df.index.values)
vindex = random.choice(vindex_lst)
video_val = video_df.loc[vindex].values

y_pr = annml.predict(video_val)
print("prediction:", y_pr)

annml.evaluate_model()
