import numpy as np
import cvxpy as cp
import gurobipy as gp

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def logit(y):
    if y>0.999:
        return 30
    if y<0.00001:
        return -40
    return np.log(y/(1-y))


def find_best_s(w_list, b_list, hidden_m_list, gamma_list, beta_list,
                u_list, var_list, epision, x: np.ndarray, family_samples: np.ndarray, zero_value, alpha1=0.99, alpha2=0.1, c = 1
                , topk=100000, verbose= False, initial_value=None):
    '''
    :param w_list: [70->30, 30->20, 20->10, 10->1]
    :param b_list: [1,         1,       1,      1]
    :param hidden_m_list: [30, 20, 10, 1]
    :param gamma_list: [30, 20, 10]
    :param beta_list:  [30, 20, 10]
    :param u_list:    [30, 20, 10]
    :param var_list: [30, 20, 10]
    :param epision: float
    :param x: (m,)
    :param family_samples: [x1, x2, x3]
    :param zero_value: (m,)
    :param alpha: float
    :return: s
    '''
    L = len(w_list)
    assert L == len(b_list) and L == len(hidden_m_list) and L == len(gamma_list) + 1 and L == len(beta_list) + 1 and \
        L == len(u_list) + 1 and L == len(var_list) + 1
    assert x.shape == zero_value.shape

    Ub, Lb = 20, -20
    if family_samples.shape[0] >= 1:
        input_x = np.concatenate([x.reshape(1, -1), family_samples], axis=0)
        bsz = input_x.shape[0]
        c_score = np.zeros((bsz,), dtype=np.float32)
        c_score[0] = 1
        c_score[1:] += c / family_samples.shape[0]


    else:
        input_x = x.reshape(1, -1)
        bsz = input_x.shape[0]
        c_score = np.zeros((bsz,), dtype=np.float32)
        c_score[0] = 1

    m = input_x.shape[1]

    vars = cp.Variable((1, m), integer=True, value=initial_value)
    epi = cp.Variable((bsz, 1))
    x_bar = cp.multiply(input_x, 1 - vars) + cp.multiply(vars, zero_value.reshape(1, -1))
    x_list = []
    x_list.append(x_bar)  
    constraints = [vars>=0, vars<=1, cp.sum(vars) <= topk]

   
    reduce_index_list = np.where(np.sum(input_x, axis=0) == 0)[0]
    for index in reduce_index_list:
        constraints.append(vars[:, index] ==0)


    for i in range(1, L):

        x_p = cp.Variable((bsz, hidden_m_list[i - 1]))
        x_n = cp.Variable((bsz, hidden_m_list[i - 1]))
        z = cp.Variable((bsz, hidden_m_list[i - 1]), integer=True)
        constraints.extend([
            z>=0, z<=1, x_p>=0, x_n >= 0, x_p <= cp.multiply(Ub, z), x_n <= cp.multiply(-Lb, (1-z)),
            x_p - x_n == cp.multiply(gamma_list[i-1].reshape(1, -1),
                                     (x_list[-1] @ w_list[i - 1] + b_list[i - 1].reshape(1, -1) - u_list[i - 1].reshape(1, -1))/np.sqrt(var_list[i-1] + epision).reshape(1, -1)) + beta_list[i-1].reshape(1, -1)
        ])

        x_list.append(x_p)
    constraints.append(x_list[-1] @ w_list[-1] + b_list[-1] <= logit(alpha1))
    constraints.append(epi >=0 )
    constraints.append(epi >= x_list[-1] @ w_list[-1] + b_list[-1] - logit(alpha2))
    objective = cp.Minimize(c_score.reshape(1, -1) @ epi)

    problem = cp.Problem(objective, constraints)

    env = gp.Env()
    env.setParam('TimeLimit', 6*60)
    problem.solve(solver=cp.GUROBI, verbose=verbose, env=env)    
    print(problem.status)
    print("Opt Value：", problem.value)
    print("Opt Solution：", vars.value)
    print('logit of input_x', (x_list[-1] @ w_list[-1] + b_list[-1]).value)    
    return vars.value.reshape(-1)