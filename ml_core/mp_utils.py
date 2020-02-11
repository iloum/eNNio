import random
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
import data_preprocessor.data_preprocessor as preproc
import pickle

def my_train_test_split(percentage, df):
    test_idx_list = list()
    test_url_list = list()

    original_list_of_indexes = list(df.index.values)

    total_items, _ = df.shape
    required_test_items = np.round(percentage*total_items)

    while len(test_idx_list)<required_test_items:
        #select random item
        item_idx = random.choice(original_list_of_indexes)
        item_url = df.at[item_idx, "Url"]
        if item_url not in test_url_list:
            test_url_list.append(item_url)
            test_idx_list.extend(list(df.index[df['Url'] == item_url]))

    train_idx_list = [x for x in original_list_of_indexes if x not in test_idx_list]

    return train_idx_list, test_idx_list


def custom_train_test_split(v_ftrs, a_ftrs, m_ftrs, test_size, x_scl, y_scl, random_state):
    random.seed(random_state)
    train_list, test_list = my_train_test_split(test_size, m_ftrs)
    video_train_df = v_ftrs.loc[train_list]
    audio_train_df = a_ftrs.loc[train_list]
    video_test_df = v_ftrs.loc[test_list]
    audio_test_df = a_ftrs.loc[test_list]

    video_train_df.head()

    video_train_vls = video_train_df.values
    audio_train_vls = audio_train_df.values
    video_test_vls = video_test_df.values
    audio_test_vls = audio_test_df.values

    video_train = x_scl.transform(video_train_vls)
    audio_train = y_scl.transform(audio_train_vls)
    video_test = x_scl.transform(video_test_vls)
    audio_test = y_scl.transform(audio_test_vls)
    return video_train, video_test, audio_train, audio_test


def model_voter(new_video_ftrs, eval_video_results_df):
    '''
    it is used to find the model with the best results in the evaluation dataset constructed by the users
    :param new_video_ftrs: dataframe with the features of the new video
    :param eval_video_results_df: dataframe with the features of the evaluation videos and also a column
    model_winner which specifies which model was preferred
    :return: the most voted model in a neighbor of 5 videos
    '''
    mdl_winners = list(eval_video_results_df['model_winner'].values)
    eval_video_results_df_proc = eval_video_results_df.drop(['model_winner'], axis=1)
    eval_video_ftrs = eval_video_results_df_proc.values

    neigh = KNeighborsClassifier(n_neighbors=5, algorithm="brute", p=2)
    neigh.fit(eval_video_ftrs, mdl_winners)

    video_new_nparray = new_video_ftrs.values
    size = video_new_nparray.shape[0]
    video_new_nparray_reshaped = video_new_nparray.reshape((1, size))

    knn_predict = neigh.predict(video_new_nparray_reshaped)

    return knn_predict


if __name__=='__main__':
    video_path = "D:\\Programming\\DataScience\\MasterDS\\Multimodal\\SemesterProject\\ennIO\\data\\video_features_df_{ftlist_[lbps,hogs,colors,flow],width_300,step_3}.pkl"

    video_df = pickle.load(open(video_path, "rb"))

    vindex_lst = list(video_df.index.values)
    vindex = random.choice(vindex_lst)
    video_val = video_df.loc[vindex]

    video_df['model_winner'] = 1

    winner = model_voter(video_val, video_df)
    print(winner)
