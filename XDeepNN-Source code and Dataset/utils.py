from collections import defaultdict
import itertools

import numpy as np
import torch
from sklearn.cluster import KMeans

def get_zero_value(m):
    if isinstance(m, np.ndarray):
        m = m.shape[-1]
    return np.zeros((m,), dtype=np.float32)

def one_hot(n_dim, x):

    result = np.zeros((n_dim, ), dtype=np.float32)
    result[x] = 1
    return result

def find_similar_samples(input_tensor, matrix_tensor, n, tolerance = 2.):
    # Calculate distances between input tensor and all rows in the matrix tensor
    distances = torch.linalg.norm(matrix_tensor - input_tensor, dim=1)
    value, sort_idx = distances.sort()
    sort_idx = sort_idx[: n]

    if n <=1:
        return matrix_tensor[sort_idx], distances[sort_idx]

    final_sort_idx = []
    for idx in sort_idx:
        if distances[idx] <= tolerance:
            final_sort_idx.append(idx.item())

    if len(final_sort_idx) <= 1:
        return matrix_tensor[sort_idx[:1]], distances[sort_idx[:1]]

    return matrix_tensor[final_sort_idx], distances[final_sort_idx]


from sklearn.cluster import DBSCAN
def split_x_test_by_distance_DBSCAN(X_test, max_diameter=2.0, min_samples=2):

    # Initialize the DBSCAN algorithm with the maximum distance and minimum samples
    dbscan = DBSCAN(eps=max_diameter, min_samples=min_samples)

    # Fit the algorithm to the matrix
    dbscan.fit(X_test)

    # Get the cluster labels for each row
    labels = dbscan.labels_

    # Get the indices of the core samples
    core_indices = dbscan.core_sample_indices_

    # Get the coordinates of all samples
    all_coords = dbscan.components_

    # Get the center coordinates of each cluster
    centers = [np.mean(all_coords[labels[core_indices] == label], axis=0) for label in (set(labels) - {-1})]

    # Create a dictionary to store the indices of the rows and their distances to the center in each cluster
    clusters = {}
    for i, label in enumerate(labels):
        if label not in clusters:
            clusters[label] = {"indices": [], "distances": []}
        clusters[label]["indices"].append(i)
        if i in core_indices:
            center = centers[label]
            distance = np.linalg.norm(X_test[i] - center)
            clusters[label]["distances"].append(distance)
        else:
            clusters[label]["distances"].append(None)

    return clusters
def get_s_and_d(idx, clusters):
    s = []
    d = []
    idx_label = None

    # find the cluster label of the given index
    for label, data in clusters.items():
        if idx in data["indices"]:
            idx_label = label
            break

    # find the indices in the same and different clusters as the given index
    for label, data in clusters.items():
        if label == idx_label:
            s = data["indices"]
        else:
            d.extend(data["indices"])

    d = list(set(d) - set(s))

    return s, d

def get_s_and_d_Matrix(idx, clusters, Matrix):
    s, d = get_s_and_d(idx, clusters)
    return Matrix[s], Matrix[d]

def sample_family_sample(family, family2samplevector, sample_size):
    result = family2samplevector[family]
    np.random.shuffle(result)
    return result[: sample_size]



def find_familial_sample(sample_idx: int, sample2family, family2samplevector, sample_size):

    result = []
    
    family_list = sample2family[sample_idx]
    
    if len(family_list) == 0:
        return result, None
    

    if len(family_list) == 1:

        temp_family = family_list[0]
    else:

        temp_family = family_list[0]
        for family in family_list:
            length = len(family2samplevector[family])
            if length == 0:
                continue

            if length > len(family2samplevector[temp_family]):
                temp_family = family
                continue

            if length >= 2 and length < 100:
                temp_family = family
                continue

            temp_family = family
    

    return sample_family_sample(temp_family, family2samplevector, sample_size), temp_family
