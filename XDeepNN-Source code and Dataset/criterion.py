import torch
import numpy as np


def original_output(model, x: torch.Tensor):
    model.eval()
    x = x.view(1, -1)
    y = model(x).view(-1)
    return y

def after_s_output(model, s: np.ndarray, x: torch.Tensor, zero_value: np.ndarray):
    s = torch.from_numpy(s).float()
    zero_value = torch.from_numpy(zero_value)
    x = x * (1 - s) + s * zero_value

    return original_output(model, x)

def BCELoss(y_pred):
    return - torch.log(1 - y_pred + 1e-5)

def suspicion_value(model, x: torch.Tensor, s: np.ndarray, zero_value: np.ndarray):
    return (BCELoss(original_output(model, x)) - BCELoss(after_s_output(model, s, x, zero_value))).item()