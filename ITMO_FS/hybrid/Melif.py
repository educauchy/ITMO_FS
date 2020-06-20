import datetime as dt
import logging

import numpy as np
from sklearn.model_selection import train_test_split

from ITMO_FS.utils.data_check import *


class Melif:

    def __init__(self, filter_ensemble, scorer=None):  # TODO scorer name
        self.ensemble = filter_ensemble
        self.__score = scorer
        self.best_score = 0
        self.best_point = []
        self.best_f = {}

    def fit(self, X, y, estimator, cutting_rule, test_size=0.3, delta=0.5, feature_names=None, points=None):
        """

        :param X:
        :param y:
        :param estimator:
        :param cutting_rule:
        :param test_size:
        :param delta:
        :param feature_names:
        :param points:
        :return:
        """
        logging.info('Running basic MeLiF\nEnsemble of :{}'.format(self.ensemble))
        feature_names = generate_features(X, feature_names)
        check_shapes(X, y)
        # check_features(features_names)
        self.__feature_names = feature_names
        self.__X = X
        self.__y = y
        self.__filter_weights = np.ones(len(self.ensemble)) / len(self.ensemble)
        self.__points = points
        self.__estimator = estimator
        self.__cutting_rule = cutting_rule

        self.__delta = delta
        # logging.info("Estimator: {}".format(estimator))
        # logging.info(
        #     "Optimizer greedy search, optimizing measure is {}".format(self.__score))  # TODO add optimizer and quality measure
        # time = dt.datetime.now()
        # logging.info("time:{}".format(time))
        check_cutting_rule(cutting_rule)
        self._train_x, self._test_x, self._train_y, self._test_y = train_test_split(self.__X, self.__y,
                                                                                    test_size=test_size)
        nu = self.ensemble.score(self.__X, self.__y, self.__feature_names)

        if self.__points is None:
            self.__points = [self.__filter_weights]
        best_point = self.__points[0]

        n = dict(zip(nu.keys(), self.__measure(np.array(list(nu.values())), best_point)))
        self.selected_features = self.__cutting_rule(n)
        self.best_f = {i: nu[i] for i in self.selected_features}

        self.__search(best_point, nu)
        # logging.info('Footer')
        # logging.info("Best point:{}".format(self.best_point))
        # logging.info("Best Score:{}".format(self.best_score))
        # logging.info('Top features:')
        # for key, value in sorted(self.best_f.items(), key=lambda x: x[1], reverse=True):
        #     logging.info("Feature: {}, value: {}".format(key, value))

    def transform(self, X):
        if type(X) is np.ndarray:
            return X[:, self.selected_features]
        else:
            return X[self.selected_features]

    def fit_transform(self, X, y, estimator, cutting_rule, test_size=0.3, delta=0.5, feature_names=None, points=None):
        self.fit(X, y, estimator, cutting_rule, test_size, delta, feature_names, points)
        return self.transform(X)

    def predict(self, X):
        return self.__estimator.predict(self.transform(X))

    def __search(self, point, features):
        i = 0
        points = [point]
        time = dt.datetime.now()
        while i < len(points):
            point = points[i]
            # logging.info('Time:{}'.format(dt.datetime.now() - time))
            # logging.info('point:{}'.format(point))
            self.__values = np.array(list(features.values()))
            n = dict(zip(features.keys(), self.__measure(self.__values, point)))
            self.selected_features = self.__cutting_rule(n)
            new_features = {i: features[i] for i in self.selected_features}
            if new_features == {}:
                break  # TODO rewrite that thing
            self.__estimator.fit(self._train_x[:, self.selected_features], self._train_y)
            predicted = self.__estimator.predict(self._test_x[:, self.selected_features])
            score = self.__score(self._test_y, predicted)
            # logging.info('Score at current point : {}'.format(score))
            if score > self.best_score:
                self.best_score = score
                self.best_point = point
                self.best_f = new_features
                points += self.__get_candidates(point, self.__delta)
            i += 1

    def __get_candidates(self, point, delta=0.1):
        candidates = np.tile(point, (len(point) * 2, 1)) + np.vstack(
            (np.eye(len(point)) * delta, np.eye(len(point)) * -delta))
        return list(candidates)

    def __score_features(self, nu, candidate):
        n = dict(zip(nu.keys(), self.__measure(nu, candidate)))
        scores = self.__cutting_rule(n)
        keys = list(scores.keys())
        self.__estimator.fit(self._train_x[list(scores.keys())], self._train_y)
        return self.__score(self._test_y, self.__estimator.predict(self._test_x[keys]))

    def __measure(self, nu, weights):
        return np.dot(nu, weights)