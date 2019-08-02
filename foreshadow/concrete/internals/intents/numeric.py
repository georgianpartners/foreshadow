"Numeric intent."

from functools import partial
from .base import BaseIntent
from foreshadow.metrics import (
    num_valid,
    unique_heur,
    is_numeric,
    is_string,
)
import pandas as pd


class Numeric(BaseIntent):
    """Defines a numeric column type."""

    confidence_computation = {
        num_valid: 0.25,
        partial(unique_heur, invert=True): 0.25,
        is_numeric: 0.25,
        partial(is_string, invert=True): 0.25,
    }

    def fit(self, X, y=None, **fit_params):
        """Empty fit.
        Args:
            X: The input data
            y: The response variable
            **fit_params: Additional parameters for the fit
        Returns:
            self
        """
        return self

    def transform(self, X, y=None):
        """Convert a column to a numeric form.
        Args:
            X: The input data
            y: The response variable
        Returns:
            A column with all rows converted to numbers.
        """
        return X.apply(pd.to_numeric, errors="coerce")
