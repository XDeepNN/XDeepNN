import torch

class MLP(torch.nn.Module):
    def __init__(self, m, hidden_m_list, eps=1e-5):
        super(MLP, self).__init__()
        self.hidden_m_list = hidden_m_list
        self.eps = eps
        self.model_list_ = []

        hidden_m_old = m
        for i in range(len(hidden_m_list)):
            self.model_list_.append(torch.nn.Linear(hidden_m_old, hidden_m_list[i]))
            hidden_m_old = hidden_m_list[i]
            if i != len(hidden_m_list) - 1:
                self.model_list_.append(torch.nn.BatchNorm1d(hidden_m_list[i], eps=eps, affine=True))
                self.model_list_.append(torch.nn.ReLU())

        self.seq = torch.nn.Sequential(*self.model_list_)
    def forward(self, x):

        return torch.sigmoid(self.seq(x))

    def get_more_detail(self, x):
        for model in self.model_list_:
            x = model(x)
            if isinstance(model, torch.nn.ReLU):
                print(x)
        return x
    def get_logit(self, x):
        return self.seq(x)


def get_corresponding_parameter_from_model(model):
    model.eval()
    w_list, b_list = [], []
    u_list, var_list = [], []
    gamma_list, beta_list = [], []
    for layer in model.model_list_:
        if isinstance(layer, torch.nn.ReLU):
            continue
        if isinstance(layer, torch.nn.BatchNorm1d):
            u_list.append(layer.running_mean.detach().numpy())
            var_list.append(layer.running_var.detach().numpy())
            gamma_list.append(layer.weight.detach().numpy())
            beta_list.append(layer.bias.detach().numpy())
            continue
        w_list.append(layer.weight.detach().numpy().transpose([1,0]))
        b_list.append(layer.bias.detach().numpy().reshape(-1))
    w_list[-1].reshape(-1)
    return w_list, b_list, model.hidden_m_list, gamma_list, beta_list, u_list, var_list, model.eps