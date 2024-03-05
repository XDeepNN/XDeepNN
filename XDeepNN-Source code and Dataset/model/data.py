import torch
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np

def data_preprocess():

    matrix = pd.read_csv('your data path', header=None).values
    label = matrix[:, -1]
    matrix = matrix[:, :-1]

    return matrix, label.reshape(-1, 1)

def get_dataloader(bsz, seed=0):

    Matrix, label = data_preprocess()

    x_data = torch.from_numpy(Matrix).float()
    y_data = torch.from_numpy(label.reshape(-1, 1)).float()

    X_train, X_test, Y_train, Y_test = train_test_split(x_data, y_data, test_size=0.2, random_state=seed)

    dataloader = DataLoader(TensorDataset(X_train, Y_train), batch_size=bsz, shuffle=True)
    test_dataloader = DataLoader(TensorDataset(X_test, Y_test), batch_size=bsz, shuffle=False)
    return X_train.numpy(), X_test.numpy(), Y_train.numpy(), Y_test.numpy(), dataloader, test_dataloader