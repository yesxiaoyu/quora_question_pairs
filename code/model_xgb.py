
# coding: utf-8

import pandas as pd
import numpy as np
from scipy import sparse as ssp
from sklearn.cross_validation import KFold
from sklearn.datasets import dump_svmlight_file,load_svmlight_file
from sklearn.utils import resample,shuffle
from sklearn.preprocessing import MinMaxScaler
from utils import _load, _save
from sklearn.metrics import log_loss
import xgboost as xgb
seed=1024
np.random.seed(seed)

train_difflib = pd.read_csv('train_feature_difflib.csv')
train_embedding = pd.read_csv('train_feature_embedding.csv')
train_fuzz = pd.read_csv('train_feature_fuzz.csv')
train_len = pd.read_csv('train_feature_len.csv')
train_match = pd.read_csv('train_feature_match.csv')
train_match_2 = pd.read_csv('train_feature_match_2.csv')
train_oof = pd.read_csv('train_feature_oof.csv')
train_simhash = pd.read_csv('train_feature_simhash.csv')

train_graph_clique = pd.read_csv('train_feature_graph_clique.csv')
train_graph_pagerank = pd.read_csv('train_feature_graph_pagerank.csv')
train_graph_freq = pd.read_csv('train_feature_graph_question_freq.csv')
train_graph_intersect = pd.read_csv('train_feature_graph_intersect.csv')

train = pd.concat([
        train_difflib,
        train_embedding,
        train_fuzz,
        train_len,
        train_match,
        train_match_2,
        train_oof,
        train_simhash,
        
        train_graph_clique,
        train_graph_pagerank,
        train_graph_freq,
        train_graph_intersect,
    ], axis=1)

test_difflib = pd.read_csv('test_feature_difflib.csv')
test_embedding = pd.read_csv('test_feature_embedding.csv')
test_fuzz = pd.read_csv('test_feature_fuzz.csv')
test_len = pd.read_csv('test_feature_len.csv')
test_match = pd.read_csv('test_feature_match.csv')
test_match_2 = pd.read_csv('test_feature_match_2.csv')
test_oof = pd.read_csv('test_feature_oof.csv')
test_simhash = pd.read_csv('test_feature_simhash.csv')

test_graph_clique = pd.read_csv('test_feature_graph_clique.csv')
test_graph_pagerank = pd.read_csv('test_feature_graph_pagerank.csv')
test_graph_freq = pd.read_csv('test_feature_graph_question_freq.csv')
test_graph_intersect = pd.read_csv('test_feature_graph_intersect.csv')

test = pd.concat([
        test_difflib,
        test_embedding,
        test_fuzz,
        test_len,
        test_match,
        test_match_2,
        test_oof,
        test_simhash,
        
        test_graph_clique,
        test_graph_pagerank,
        test_graph_freq,
        test_graph_intersect,
    ], axis=1)


y = pd.read_csv('../../input/train.csv')['is_duplicate']

n_fold = 5
kf = KFold(n=X.shape[0], n_folds=n_fold, shuffle=True, random_state=2017)

params = {}
params["objective"] = "binary:logistic"
params['eval_metric'] = 'logloss'
params["eta"] = 0.04
params["subsample"] = 0.8
params["min_child_weight"] = 2
params["colsample_bytree"] = 0.9
params["max_depth"] = 8
params["silent"] = 1
params["seed"] = 1632
# params["updater"] = "grow_gpu"

totalpreds = []
n = 0
for index_train, index_eval in kf:
    
    x_train, x_eval = train.iloc[index_train], train.iloc[index_eval]
    y_train, y_eval = y[index_train], y[index_eval]
    
    d_train = xgb.DMatrix(x_train, label=y_train)
    d_valid = xgb.DMatrix(x_eval, label=y_eval)
    watchlist = [(d_valid, 'valid')]
    
    bst = xgb.train(params, d_train, 40000, watchlist, early_stopping_rounds=100, verbose_eval=100)

    print('start predicting on test...')
    testpreds = bst.predict(xgb.DMatrix(test))
    if n > 0:
        totalpreds = totalpreds + testpreds
    else:
        totalpreds = testpreds
    
    bst.save_model('xgb_model_fold_{}.model'.format(n))
    n += 1

totalpreds = totalpreds / n
test_id = pd.read_csv('../../input/test.csv')['test_id']
sub = pd.DataFrame()
sub['test_id'] = test_id
sub['is_duplicate'] = pd.Series(totalpreds)
sub.to_csv('xgb_prediction.csv', index=False)


a = 0.174264424749 / 0.369197853026
b = (1 - 0.174264424749) / (1 - 0.369197853026)
trans = sub.is_duplicate.apply(lambda x: a * x / (a * x + b * (1 - x)))
sub['is_duplicate'] = trans
sub.to_csv('xgb_prediction_trans.csv', index=False)