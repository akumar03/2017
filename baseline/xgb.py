'''
Baseline solution for the ACM Recsys Challenge 2017
using XGBoost

by Daniel Kohlsdorf
'''

from model import *
from parser import *

from test import *
import os

mingw_path = 'C:\\Program Files\\mingw-w64\\x86_64-5.3.0-posix-seh-rt_v4-rev0\\mingw64\\bin'
os.environ['PATH'] = mingw_path + ';' + os.environ['PATH']
import xgboost as xgb
import numpy as np
import multiprocessing
from recommendation_worker import *

import random

hello()

print(" --- Recsys Challenge 2017 Baseline --- ")

N_WORKERS = 5
USERS_FILE = "C:\\Users\\anoopk\\Dropbox\\recsys\\data_2017\\users.csv"
ITEMS_FILE = "C:\\Users\\anoopk\\Dropbox\\recsys\\data_2017\\items.csv"
INTERACTIONS_FILE = "C:\\Users\\anoopk\\Dropbox\\recsys\\data_2017\\interactions.csv"
TARGET_USERS = "C:\\Users\\anoopk\\Dropbox\\recsys\\data_2017\\targetUsers.csv"
TARGET_ITEMS = "C:\\Users\\anoopk\\Dropbox\\recsys\\data_2017\\targetItems.csv"

'''
1) Parse the challenge data, exclude all impressions
   Exclude all impressions
'''

(header_users, users) = select(USERS_FILE, lambda x: True, build_user, lambda x: int(x[0]))
(header_items, items) = select(ITEMS_FILE, lambda x: True, build_item, lambda x: int(x[0]))

builder = InteractionBuilder(users, items)
(header_interactions, interactions) = select(
    INTERACTIONS_FILE,
    lambda x: x[2] != '0',
    builder.build_interaction,
    lambda x: (int(x[0]), int(x[1]))
)

'''
2) Build recsys training data
'''
data = np.array([interactions[key].features() for key in interactions.keys()])
labels = np.array([interactions[key].label() for key in interactions.keys()])
dataset = xgb.DMatrix(data, label=labels)
dataset.save_binary("recsys2017.buffer")

'''
3) Train XGBoost regression model with maximum tree depth of 2 and 25 trees
'''
evallist = [(dataset, 'train')]
param = {'bst:max_depth': 2 , 'bst:eta': 0.1, 'silent': 1, 'objective': 'reg:linear'}
param['nthread'] = 4
param['eval_metric'] = 'rmse'
param['base_score'] = 0.0
num_round = 25
bst = xgb.train(param, dataset, num_round, evallist)
bst.save_model('recsys2017.model')

'''
4) Create target sets for items and users
'''
target_users = []
for line in open(TARGET_USERS):
    target_users += [int(line.strip())]
target_users = set(target_users)

target_items = []
for line in open(TARGET_ITEMS):
    target_items += [int(line.strip())]

'''
5) Schedule classification
'''

# classify_worker(target_items,target_users,items,users,"solution.csv",bst)
bucket_size = len(target_items) / N_WORKERS
start = 0
jobs = []
for i in range(0, N_WORKERS):
    stop = int(min(len(target_items), start + bucket_size))
    filename = "solution_" + str(i) + ".csv"
    process = multiprocessing.Process(target=classify_worker,
                                      args=(target_items[start:stop], target_users, items, users, filename, bst))
    jobs.append(process)
    start = stop

if __name__ == '__main__':
    for j in jobs:
            j.start()

    for j in jobs:
        j.join()
