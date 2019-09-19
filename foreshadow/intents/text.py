"""Text intent."""

from functools import partial

from foreshadow.metrics import is_numeric, is_string, num_valid, \
    unique_heur, MetricWrapper2

from .base import BaseIntent


class Text(BaseIntent):
    """Defines a text column type."""

    confidence_computation = {
        MetricWrapper2(num_valid): 0.25,
        MetricWrapper2(unique_heur): 0.25,
        MetricWrapper2(is_numeric, invert=True): 0.25,
        MetricWrapper2(is_string): 0.25,
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
        """Convert a column to a text form.

        Args:
            X: The input data
            y: The response variable

        Returns:
            A column with all rows converted to text.

        """
        return X.astype(str)
