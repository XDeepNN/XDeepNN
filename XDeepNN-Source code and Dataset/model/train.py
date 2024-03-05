import os
import pickle
import joblib
import numpy as np

import torch
import torch.nn.functional as F
from torch.utils.data import TensorDataset, DataLoader

from .deep_model import MLP

def seed_all(seed):
    import random
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
seed_all(1)

def train(m, hidden_m_list, epision, dataloader, epochs, lr):
    model = MLP(m, hidden_m_list, epision)

    criterion = torch.nn.BCELoss()    
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    model.train()
    for epoch in range(epochs):
        for i, (x, y) in enumerate(dataloader):
            y_pred = model(x)
            loss = criterion(y_pred, y)
            print('Epoch:{}, Loss:{}'.format(epoch, loss.item()))
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    return model