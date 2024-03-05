from feature_importance import find_best_s
from criterion import *

import torch
import numpy as np

from model.deep_model import get_corresponding_parameter_from_model
from model.train import train
from model.data import get_dataloader

from utils import find_similar_samples, get_zero_value

def seed_all(seed):
    import random
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
seed_all(1)
def get_zero_value(m):
    if isinstance(m, np.ndarray):
        m = m.shape[-1]
    return np.zeros((m,), dtype=np.float32)

epochs = 50
lr = 0.01
m = 73
epision = 1e-5

bsz = 512
sample_size = 5
tolerance = 2.
alpha1 = 0.8
alpha2 = 0.1
c = 0.5
k = 10
hidden_m_list = [30, 20, 10, 1]
X_train, X_test, Y_train, Y_test, dataloader, test_dataloader = get_dataloader(bsz)

model = train(m, hidden_m_list, epision, dataloader, epochs, lr)

mal_X_train = X_train[Y_train.reshape(-1) == 1]
X_test_mal = X_test[Y_test.reshape(-1) == 1]

def get_all_model_output(model, X_train: np.ndarray, mal_X_train, x: np.ndarray, alpha1, alpha2, c,topk, sample_size,
                         epision=1e-5, initial_value=None):


    similar_samples, length = find_similar_samples(torch.from_numpy(x), torch.from_numpy(mal_X_train), sample_size)
    zero_value = get_zero_value(X_train)
    w_list, b_list, hidden_m_list, gamma_list, beta_list, \
    u_list, var_list, eps = get_corresponding_parameter_from_model(model)
    initial_value = np.array(initial_value, dtype=np.int64).reshape(1, -1)
    s = find_best_s(w_list, b_list, hidden_m_list, gamma_list, beta_list,
                    u_list, var_list, epision, x, similar_samples.numpy(), zero_value, alpha1=alpha1, alpha2=alpha2, c=c,
                    topk=topk, initial_value=initial_value)

    return s, after_s_output(model, s.astype(np.float32), torch.from_numpy(x), zero_value).item()

x = X_test_mal[0]
get_all_model_output(model, X_train, mal_X_train, x, alpha1, alpha2, c, k, sample_size,
                         epision=1e-5, initial_value=None)