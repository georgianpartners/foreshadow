"""Resolver module that computes the intents for input data."""

from foreshadow.config import get_intents
from foreshadow.core.preparerstep import PreparerStep
from foreshadow.transformers.core.smarttransformer import SmartTransformer


class IntentResolver(PreparerStep):
    """Apply intent resolution to each column.

    Params:
        *args: args to PreparerStep constructor.
        **kwargs: kwargs to PreparerStep constructor.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, use_single_pipeline=True, **kwargs)

    def get_mapping(self, X):
        """Return the mapping of transformations for the DataCleaner step.

        Args:
            X: input DataFrame.

        Returns:
            Mapping in accordance with super.

        """
        return self.separate_cols(
            transformers=[
                [Resolver(column_sharer=self.column_sharer)] for c in X
            ],
            X=X,
        )


class Resolver(SmartTransformer):
    """Determine the intent for a particular column.

    Params:
        **kwargs: kwargs to pass to individual intent constructors

    """

    validate_wrapped = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _resolve_intent(self, X, y=None):
        """Pick the intent with the highest confidence score.

        Note:
            In the case of ties, the intent `defined first \
            <https://docs.python.org/3/library/functions.html#max>`_ in the
            config list is chosen, the priority order is defined by the config
            file `resolver` section.

        Return:
            The intent class that best matches the input data.

        .. # noqa: S001

        """
        return max(get_intents(), key=lambda intent: intent.get_confidence(X))

    def resolve(self, X, *args, **kwargs):
        """Pick the appropriate transformer if necessary.

        Note:
            Column info sharer is set based on the chosen transformer.

        Args:
            X: input observations
            *args: args to pass to resolve
            **kwargs: params to resolve

        """
        super().resolve(X, *args, **kwargs)
        column_name = X.columns[0]
        self.column_sharer[
            "intent", column_name
        ] = self.transformer.__class__.__name__

    def pick_transformer(self, X, y=None, **fit_params):
        """Get best intent transformer for a given column.

        Note:
            This function also sets the column_sharer

        Args:
            X: input DataFrame
            y: input labels
            **fit_params: fit_params

        Returns:
            Best intent transformer.

        """
        intent_class = self._resolve_intent(X, y=y)

        return intent_class()