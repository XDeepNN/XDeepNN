import numpy as np
from sklearn import metrics


class Indicator(object):
    def __init__(self, pred, y_test):
        self.pred = pred
        self.y_test = y_test
        self.TP = 0
        self.FP = 0
        self.TN = 0
        self.FN = 0
        self.Accuracy = 0
        self.Precison = 0
        self.Recall = 0
        self.F_meature = 0
        self.Specific = 0
        self.mcc = 0
        self.tpr = 0
        self.fpr = 0
        self.auc = 0

       
        for i in range(len(self.pred)):
            if (self.pred[i] == self.y_test[i] and self.y_test[i] == 1):
                self.TP += 1
            elif (self.pred[i] == self.y_test[i] and self.y_test[i] == 0):
                self.TN += 1
            elif (self.pred[i] != self.y_test[i] and self.y_test[i] == 0):
                self.FP += 1
            elif (self.pred[i] != self.y_test[i] and self.y_test[i] == 1):
                self.FN += 1
        
        self.Precision = metrics.precision_score(y_true=self.y_test, y_pred=self.pred)        
        self.Recall = metrics.recall_score(y_true=self.y_test, y_pred=self.pred)        
        self.F_meature = metrics.f1_score(y_true=self.y_test, y_pred=self.pred, average='macro')
        self.Accuracy = metrics.accuracy_score(self.y_test, y_pred=self.pred)

       
        self.Specific = (self.TN / (self.TN + self.FP))

        
        self.TPR = self.TP / (self.TP + self.FN)
        self.FPR = self.FP / (self.FP + self.TN)

    
        self.MCC = metrics.matthews_corrcoef(y_true=y_test.astype('int'), y_pred=pred)
    def get_acc(self):
        return self.Accuracy
    def get_precision(self):
        return self.Precision
    def get_recall(self):
        return self.Recall
    def get_fmeature(self):
        return self.F_meature
    def get_specific(self):
        return self.Specific

    def get_tpr(self):
        return self.TPR
    def get_fpr(self):
        return self.FPR

    def get_mcc(self):
        return self.MCC

    def get_auc(self):
        AUC = 0
        m = self.y_test.shape[0]
        pos_num = (self.TP + self.FN)
        neg_num = (self.TN + self.FP)
        x = np.zeros([m + 1])
        y = np.zeros([m + 1])

        x[0] = 1
        y[0] = 1

        for i in range(1, m):
            TP = 0
            FP = 0
            for j in range(i, m):
                if (self.pred[j] == self.y_test[j] and self.y_test[j] == 1):
                    TP += 1
                elif (self.pred[j] != self.y_test[j] and self.y_test[j] == 0):
                    FP += 1
            # print(TP)
            x[i] = FP / neg_num
            y[i] = TP / pos_num
            AUC += (y[i] + y[i - 1]) * (x[i - 1] - x[i]) / 2

        x[m] = 0
        y[m] = 0
        AUC += y[m - 1] * x[m - 1] / 2

        self.auc = AUC
        return self.auc 


def get_indicators(pred, label, indicator_name_list):
    '''
    :param pred: [0,1,1,...] ndarray(N,)
    :param label: [0,1,....] ndarray(N,)
    :param indicator_name_list: ['acc', 'auc', ...]
    :return: list of indicators [acc, auc, ...]
    '''
    ind = Indicator(pred, label)
    result_list = []
    for name in indicator_name_list:
        method_name = 'get_{}()'.format(name)
        result = eval('ind.{}'.format(method_name))
        result_list.append(result)
    return result_list

def format_print(name_list, result):
    for name, result in zip(name_list, result):
        print('{} : {}'.format(name, result))


def format_str(name_list, result):
    str = ''
    for name, result in zip(name_list, result):
        str += '{} : {} \n'.format(name, result)
    return str