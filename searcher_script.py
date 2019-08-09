from foreshadow.preparer import DataPreparer
from foreshadow.steps import CleanerMapper
from foreshadow.steps import IntentMapper
from foreshadow.steps import Preprocessor
from foreshadow.columnsharer import ColumnSharer
import pandas as pd

from sklearn.model_selection import RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

import sklearn.datasets as dt

from foreshadow.smart import Scaler

from foreshadow.utils.testing import debug; debug()

from hyperopt import hp
import hyperopt.pyll.stochastic as stoch

from sklearn.model_selection import ParameterSampler
from sklearn.model_selection._search import BaseSearchCV
from sklearn.utils.fixes import _Mapping as Mapping, _Sequence as Sequence
import six
import numpy as np

data = dt.load_iris()

X_data = pd.DataFrame(data.data, columns=data.feature_names).iloc[:, 0]
y_data = pd.DataFrame(data.target, columns=['target'])

# cs = ColumnSharer()
# p = Preprocessor(column_sharer=cs)
s = Scaler()
lr = LogisticRegression()

pipe = Pipeline([('s', s), ('lr', lr)])

pipe.fit(X_data, y_data)

param_distributions = {
    's__transformer': hp.choice(
        's__transformer',
        [
            {
                    'class_name': 'StandardScaler',
                    'with_mean': hp.choice('with_mean', [False, True]),
            },
            {
                'class_name': 'MinMaxScaler',
                'feature_range': hp.choice('feature_range', [(0, 1), (0, 0.5)])
            }
        ]
    )
}

from sklearn.utils import check_random_state
class HyperOptSampler(object):
    def __init__(self, param_distributions, n_iter, random_state=None):
        self.param_distributions = param_distributions
        self.n_iter = n_iter
        self.random_state = random_state

    def __iter__(self):
        # check if all distributions are given as lists
        # in this case we want to sample without replacement
        rng = check_random_state(self.random_state)
        for _ in six.moves.range(self.n_iter):
            import pdb; pdb.set_trace()
            yield stoch.sample(self.param_distributions, rng=rng)

    def __len__(self):
        """Number of points that will be sampled."""
        return self.n_iter


class ShadowSearchCV(BaseSearchCV):
    def __init__(self, estimator, param_distributions, n_iter=10, scoring=None,
                 fit_params=None, n_jobs=1, iid=True, refit=True, cv=None,
                 verbose=0, pre_dispatch='2*n_jobs', random_state=None,
                 error_score='raise', return_train_score="warn"):
        self.param_distributions = param_distributions
        self.n_iter = n_iter
        self.random_state = random_state
        super().__init__(
             estimator=estimator, scoring=scoring, fit_params=fit_params,
             n_jobs=n_jobs, iid=iid, refit=refit, cv=cv, verbose=verbose,
             pre_dispatch=pre_dispatch, error_score=error_score,
             return_train_score=return_train_score)

    def _get_param_iterator(self):
        """Return ParameterSampler instance for the given distributions"""
        return HyperOptSampler(
            self.param_distributions, self.n_iter,
            random_state=self.random_state)

from hpsklearn import HyperoptEstimator, extra_trees
from hyperopt import tpe


# combinations.yaml
"""
combinations:
    X_preparer.cleaner.CHAS:
        Cleaner:
            - date:
                - p1
                - p2
            - financial
        IntentMapper:
            - Something

    X_preparer.cleaner.CHAS.CleanerMapper:
        -Something

    X_preparer.cleaner.CHAS.IntentMapper:
        -Something


    X_preparer:
        cleaner:
            CHAS:
                Cleaner:
                    date:
                        -p1
                        -p2

"""

rscv = ShadowSearchCV(pipe, param_distributions, iid=True, scoring='accuracy', n_iter=2)

# print("Train Accuracy: {}".format(accuracy_score(y_data, pipe.predict(X_data))))

rscv.fit(X_data, y_data)
results = pd.DataFrame(rscv.cv_results_)
results = results[[c for c in results.columns if all(s not in c for s in ['time', 'params'])]]


import pdb; pdb.set_trace()