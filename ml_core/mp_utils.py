import random
import numpy as np

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
    x_train_df = v_ftrs.loc[train_list]
    y_train_df = a_ftrs.loc[train_list]
    x_test_df = v_ftrs.loc[test_list]
    y_test_df = a_ftrs.loc[test_list]

    x_train_df.head()

    x_train_vls = x_train_df.values
    y_train_vls = y_train_df.values
    x_test_vls = x_test_df.values
    y_test_vls = y_test_df.values

    x_train = x_scl.transform(x_train_vls)
    y_train = y_scl.transform(y_train_vls)
    x_test = x_scl.transform(x_test_vls)
    y_test = y_scl.transform(y_test_vls)
    return x_train, x_test, y_train, y_test
