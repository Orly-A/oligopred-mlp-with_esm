import numpy as np
import pandas as pd
import datetime
from sklearn import metrics
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import RandomizedSearchCV
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import f1_score
from sklearn.metrics import roc_auc_score, make_scorer
from sklearn.dummy import DummyClassifier
from imblearn.under_sampling import RandomUnderSampler


NUM_CV = 5
NUM_ITER = 100
UNDERSAMPLE_FACTOR = 3

def data_definition_hyp(overall_train_set):
    # overall_train_set = remove_small_groups()
    # overall_train_set = downsample_mjorities(overall_train_set)
    X = pd.DataFrame(np.vstack(overall_train_set['esm_embeddings']))
    y = overall_train_set["nsub"]
    # reduce y to 3 classes: 1, 2, 3+
    new_y = y.apply(lambda x: 1 if x == 1 else 2 if x == 2 else 0)
    groups = overall_train_set["representative"]
    cv = StratifiedGroupKFold(n_splits=NUM_CV)
    df = pd.DataFrame(np.vstack(X))
    # convert_dict = gen_converter()
    # y = y.map(convert_dict)
    return X, y, groups, cv, df, new_y


def data_definition_only_oligos(overall_train_set):
    print("This training was run only on oligomers, without monomers and dimers")
    overall_train_set1 = overall_train_set[overall_train_set.nsub != 1]
    overall_train_set_final = overall_train_set1[overall_train_set1.nsub != 2]
    overall_train_set_final = remove_small_groups(overall_train_set_final)
    X = pd.DataFrame(np.vstack(overall_train_set_final['esm_embeddings']))
    y = overall_train_set_final["nsub"]
    groups = overall_train_set_final["representative"]
    cv = StratifiedGroupKFold(n_splits=NUM_CV)
    df = pd.DataFrame(np.vstack(X))
    return X, y, groups, cv, df

def data_definition_monomers_dimers(overall_train_set):
    print("This training was run only on monomers and dimers! no oligomers")
    overall_train_set = overall_train_set[overall_train_set.nsub < 3]
    X = pd.DataFrame(np.vstack(overall_train_set['esm_embeddings']))
    y = overall_train_set["nsub"]
    groups = overall_train_set["representative"]
    cv = StratifiedGroupKFold(n_splits=NUM_CV)
    df = pd.DataFrame(np.vstack(X))
    return X, y, groups, cv, df



def remove_small_groups(overall_train_set):
    overall_train_set_no_embed = overall_train_set[["code", "nsub", "representative"]]
    overall_train_set2 = overall_train_set.copy()
    list_of_nsubs = list(set(overall_train_set2["nsub"].tolist()))
    for nsub in list_of_nsubs:
        num_of_clusts = overall_train_set_no_embed[overall_train_set_no_embed['nsub'] == nsub].groupby("representative").nunique().shape[0]
        if num_of_clusts < NUM_CV:
            print(nsub, "nsub")
            print(num_of_clusts, "num_of_clusts")
            overall_train_set2 = overall_train_set2[overall_train_set2.nsub != nsub]
    return overall_train_set2


def downsample_mjorities(overall_train_set):
    new_1_count = int(overall_train_set[overall_train_set["nsub"] == 1].shape[0]/UNDERSAMPLE_FACTOR)
    new_2_count = int(overall_train_set[overall_train_set["nsub"] == 2].shape[0]/UNDERSAMPLE_FACTOR)
    under_sample_dict = {1: new_1_count, 2: new_2_count}
    list_of_nsubs = list(set(overall_train_set["nsub"].tolist()))
    list_of_nsubs.remove(1)
    list_of_nsubs.remove(2)
    for nsub in list_of_nsubs:
        counter = int(overall_train_set[overall_train_set["nsub"] == nsub].shape[0])
        under_sample_dict[nsub] = counter
    print(under_sample_dict)
    rus = RandomUnderSampler(random_state=1, sampling_strategy=under_sample_dict)
    X, y = rus.fit_resample(overall_train_set[["code"]], overall_train_set["nsub"])
    overall_train_set = overall_train_set[overall_train_set.code.isin(X["code"].tolist())]
    return overall_train_set


def generate_grid():
    activation = ['identity', 'logistic', 'tanh', 'relu']
    learning_rate = ['constant', 'invscaling', 'adaptive']
    learning_rate_init = [0.001, 0.01, 0.1, 1]
    solver = ['sgd', 'adam']
    max_iter = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    n_iter_no_change = [5, 10, 15, 20, 30, 40]
    tol = [0.0001, 0.0005, 0.001, 0.01, 0.1, 1]
    hidden_layer_sizes = [(10,), (20,), (40,), (60,), (80,), (100,), (120,), (140,), (160,), (180,), (200,)]
    # hidden_layer_sizes = [(12, 24, 36), (40, 40, 40), (40, 40, 40, 40, 40, 40, 40, 40, 40, 40), (12, 24, 36, 48),
    #                       (24, 36, 48), (24, 36, 48, 64), (36, 48, 60, 72, 84, 96)]
    # hidden_layer_sizes = [(10,), (20,), (40,), (60,), (80,), (100,), (120,), (140,), (160,), (180,), (200,), (40,40,40)]
    alpha = [0.0001, 0.0005, 0.001, 0.01, 0.1, 1]
    batch_size = [10, 50, 80, 100, 150, 200, 250, 300, 350, 400]
    grid_params = {'activation': activation,
                   'learning_rate': learning_rate,
                   'learning_rate_init': learning_rate_init,
                   'solver': solver,
                   'max_iter': max_iter,
                   'n_iter_no_change': n_iter_no_change,
                   'tol': tol,
                   'hidden_layer_sizes': hidden_layer_sizes,
                   'alpha': alpha,
                   'batch_size': batch_size}
    return grid_params


def generate_grid_second_run_12rest():
    activation = ['identity', 'tanh']
    learning_rate = ['constant', 'adaptive']
    learning_rate_init = [0.01, 0.1]
    solver = ['adam']
    max_iter = [600, 700, 800]
    n_iter_no_change = [15, 30]
    tol = [0.001, 0.01]
    hidden_layer_sizes = [(10,), (40,), (140,), (160,), (10,10,10,10,10,10,10,10,10,10,10,),
                          (40, 40, 40), (140, 140, 140, 140, 140, 140), (160, 160, 160),
                          (10,10,10,10,40,40,40,40,140,140,140,140,160,160,160,160)]
    # hidden_layer_sizes = [(12, 24, 36), (40, 40, 40), (40, 40, 40, 40, 40, 40, 40, 40, 40, 40), (12, 24, 36, 48),
    #                       (24, 36, 48), (24, 36, 48, 64), (36, 48, 60, 72, 84, 96)]
    # hidden_layer_sizes = [(10,), (20,), (40,), (60,), (80,), (100,), (120,), (140,), (160,), (180,), (200,), (40,40,40)]
    alpha = [0.0001, 0.1]
    batch_size = [150, 350, 500, 700, 850, 1000]
    grid_params = {'activation': activation,
                   'learning_rate': learning_rate,
                   'learning_rate_init': learning_rate_init,
                   'solver': solver,
                   'max_iter': max_iter,
                   'n_iter_no_change': n_iter_no_change,
                   'tol': tol,
                   'hidden_layer_sizes': hidden_layer_sizes,
                   'alpha': alpha,
                   'batch_size': batch_size}
    return grid_params

def generate_grid_second_run_mono_dimer():
    activation = ['identity', 'tanh']
    learning_rate = ['constant', 'adaptive']
    learning_rate_init = [0.01, 0.1]
    solver = ['adam', 'sgd']
    max_iter = [500, 600, 900, 1500]
    n_iter_no_change = [15, 20, 30]
    tol = [0.001, 0.05, 1.0, 5.0]
    hidden_layer_sizes = [(10,), (20,), (40,), (120,), (160,), (10,10,10,10,10,10,10,10,10,10,10,),
                          (40, 40, 40), (120, 120, 120, 120, 120, 120), (160, 160, 160),
                          (10,10,10,10,40,40,40,40,120,120,120,120,160,160,160,160)]
    # hidden_layer_sizes = [(12, 24, 36), (40, 40, 40), (40, 40, 40, 40, 40, 40, 40, 40, 40, 40), (12, 24, 36, 48),
    #                       (24, 36, 48), (24, 36, 48, 64), (36, 48, 60, 72, 84, 96)]
    # hidden_layer_sizes = [(10,), (20,), (40,), (60,), (80,), (100,), (120,), (140,), (160,), (180,), (200,), (40,40,40)]
    alpha = [0.0008, 0.001, 0.0015]
    batch_size = [50, 70, 100, 150, 300, 400, 450, 500, 600, 700, 750, 1000]
    grid_params = {'activation': activation,
                   'learning_rate': learning_rate,
                   'learning_rate_init': learning_rate_init,
                   'solver': solver,
                   'max_iter': max_iter,
                   'n_iter_no_change': n_iter_no_change,
                   'tol': tol,
                   'hidden_layer_sizes': hidden_layer_sizes,
                   'alpha': alpha,
                   'batch_size': batch_size}
    return grid_params

def generate_grid_second_run_oligos():
    activation = ['identity', 'tanh', 'relu']
    learning_rate = ['constant', 'adaptive']
    learning_rate_init = [0.001, 0.01, 0.1]
    solver = ['adam', 'sgd']
    max_iter = [300, 500, 600, 800, 1000, 1500]
    n_iter_no_change = [10, 20]
    tol = [0.0001, 0.0005, 0.001, 0.1, 1.0, 5.0]
    hidden_layer_sizes = [(40,), (100,), (140,), (160,), (180,),(40,40,40,40,40,40,40,40,40,40,40),
                          (100, 100, 100), (140, 140, 140, 140, 140, 140), (160, 160, 160), (180, 180, 180),
                          (40,40,40,40,100,100,100,100,140,140,140,140,160,160,160,160,180,180,180,180)]
    # hidden_layer_sizes = [(12, 24, 36), (40, 40, 40), (40, 40, 40, 40, 40, 40, 40, 40, 40, 40), (12, 24, 36, 48),
    #                       (24, 36, 48), (24, 36, 48, 64), (36, 48, 60, 72, 84, 96)]
    # hidden_layer_sizes = [(10,), (20,), (40,), (60,), (80,), (100,), (120,), (140,), (160,), (180,), (200,), (40,40,40)]
    alpha = [0.001, 0.01]
    batch_size = [50, 200, 300, 500, 700, 850, 1000]
    grid_params = {'activation': activation,
                   'learning_rate': learning_rate,
                   'learning_rate_init': learning_rate_init,
                   'solver': solver,
                   'max_iter': max_iter,
                   'n_iter_no_change': n_iter_no_change,
                   'tol': tol,
                   'hidden_layer_sizes': hidden_layer_sizes,
                   'alpha': alpha,
                   'batch_size': batch_size}
    return grid_params



def hyperparam_search(grid_params, groups, X, y):
    y = y.values.astype(int)
    # le = LabelEncoder()
    # y = le.fit_transform(y)

    clf = MLPClassifier()
    print("starting the tuning")
    print(datetime.datetime.now())
    cv = StratifiedGroupKFold(n_splits=NUM_CV)
    f1_score_weighted = make_scorer(f1_score, average="weighted")
    f1_score_weighted
    adj_balanced_acc = make_scorer(metrics.balanced_accuracy_score, adjusted=True)
    adj_balanced_acc

    clf_random = RandomizedSearchCV(clf, grid_params, cv=cv, verbose=4,
                                    scoring={"f1_score": f1_score_weighted, "adjusted_balanced_accuracy": adj_balanced_acc},
                                    return_train_score=True, refit="adjusted_balanced_accuracy",
                                    n_iter=NUM_ITER, n_jobs=-1)
    clf_random.fit(X, y, groups=groups)
    print("finished tuning")
    print(datetime.datetime.now())
    print(clf_random.best_params_)
    print(clf_random.best_score_)
    print(clf_random.scorer_)
    print(NUM_ITER, "number of iterations")
    print(NUM_CV, "number of k-fold")
    return clf_random.best_params_


if __name__ == "__main__":
    # using the new clustering with 0.3 coverage:
    # overall_train_set = pd.read_pickle("/vol/ek/Home/orlyl02/working_dir/oligopred/clustering/re_clust_c0.3/train_set_c0.3.pkl")
    # using the esm_embed:
    overall_train_set = pd.read_pickle(
        "/vol/ek/Home/orlyl02/working_dir/oligopred/esmfold_prediction/train_set_c0.3.pkl")
    # index reset is important for the stratified splitting and the saving to lists
    overall_train_set.reset_index(drop=True, inplace=True)
    # X, y, groups, cv, df, new_y = data_definition_hyp(overall_train_set)
    X, y, groups, cv, df = data_definition_only_oligos(overall_train_set)
    # X, y, groups, cv, df = data_definition_monomers_dimers(overall_train_set)
    grid_params = generate_grid()
    best_params = hyperparam_search(grid_params, groups, X, y)
