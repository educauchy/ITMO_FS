import numpy as np
from sklearn.metrics import f1_score

def normalize(x):
    x = np.abs(np.array(x))
    max_ = max(x)
    min_ = max(x)
    return (x - min_) / (max_ - min_)


def cartesian(rw, cl):  # returns cartesian product for passed numpy arrays as two paired numpy array
    tmp = np.array(np.meshgrid(rw, cl)).T.reshape(len(rw) * len(cl), 2)
    return tmp.T[0], tmp.T[1]

def weight_func(model):  # weight function used in MOS testing
    return model.coef_[0]

def f1_scorer(y_true, y_pred):
    return f1_score(y_true, y_pred, average='micro')

def augmented_rvalue(X, y, k=7, theta=3):
    """
    Calculates the augmented R-value for a dataset with two classes. 

        Parameters
        ----------
        X : array-like, shape (n_samples,n_features)
            The input samples.
        y : array-like, shape (n_samples)
            The classes for the samples.
        k : int
            The amount of nearest neighbors used in the calculation.
        theta : int
            The threshold value: if from k nearest neighbors of an object more than theta of them are of a different class, 
            then this object is in the overlap region.
        Returns
        ------
        float - the augmented R-value for the dataset; the value is in the range [-1, 1].

        Notes
        -----
        For more details see `this paper <https://www.sciencedirect.com/science/article/pii/S0169743919306070>`_.

    """
    unique, counts = np.unique(y, return_counts=True)
    freq = sorted(list(zip(unique, counts)), key=lambda x: x[1], reverse=True)
    Rs = []
    Cs = []

    for label, frequency in freq:
        Cs.append(frequency)
        count = 0
        for elem in [i for i, x in enumerate(y) if x == label]:
            nearest = knn(X, y, elem, k) # TODO: should probably rewrite this using sklearn's knn or pairwise_distances
            count += np.sign(k - list(map(lambda x: y[x], nearest)).count(label) - theta)
        Rs.append(count / frequency)
    Cs = Cs[::-1]
    return np.dot(Rs, Cs) / len(X)


def knn_from_class(distances, y, index, k, cl, anyClass=False):
    """
    Returns the indices of k nearest neighbors of X[index] from the selected class.
        Parameters
        ----------
        distances : array-like, shape (n_samples, n_samples)
            The distance matrix of the input samples.
        y : array-like, shape (n_samples)
            The classes for the samples.
        index : int
            The index of an element.
        k : int
            The amount of nearest neighbors to return.
        cl : int
            The class label for the nearest neighbors.
        anyClass : bool
            If True, returns neighbors not belonging to the same class
            as X[index].

        Returns
        ------
        array-like, shape (k) - the indices of the nearest neighbors
    """
    y_c = np.copy(y)
    if anyClass:
        cl = y_c[index] + 1
        y_c[y_c != y_c[index]] = cl
    class_indices = np.nonzero(y_c == cl)[0]
    distances_class = distances[index][class_indices]
    nearest = np.argsort(distances_class)
    if y_c[index] == cl:
        nearest = nearest[1:]

    return class_indices[nearest[:k]]

def matrix_norm(M):
    """
    Calculates the norm of all rows in the matrix.
        Parameters
        ----------
        M : array-like, shape (n, m)
            The matrix.
        Returns
        -------
        array-like, shape (n) - the norms for each row in the matrix
    """
    return np.sqrt((M * M).sum(axis=1))

def l21_norm(M):
    """
    Calculates the L2,1 norm of a matrix.
        Parameters
        ----------
        M : array-like, shape (n, m)
            The matrix.
        Returns
        -------
        float - the L2,1 norm of this matrix
    """
    return matrix_norm(M).sum()

def power_neg_half(M):
    """
    Calculates M ^ (-1/2).
        Parameters
        ----------
        M : array-like, shape (n, m)
            The matrix.
        Returns
        -------
        array-like, shape (n, m) - M ^ (-1/2)
    """
    return np.sqrt(np.linalg.inv(M))

def apply_cr(cutting_rule):
    from ..filters.univariate.measures import CR_NAMES, MEASURE_NAMES
    if type(cutting_rule) is tuple:
        cutting_rule_name = cutting_rule[0]
        cutting_rule_value = cutting_rule[1]
        try:
            cr = CR_NAMES[cutting_rule_name](cutting_rule_value)
        except KeyError:
            raise KeyError("No %r cutting rule yet" % cutting_rule_name)
    elif hasattr(cutting_rule, '__call__'):
        cr = cutting_rule
    else:
        raise KeyError("%r isn't a cutting rule function or string" % cutting_rule)
    return cr
