"""Defines the Preprocessor step in the Foreshadow DataPreparer pipeline."""

from foreshadow.config import config
from foreshadow.smart import IntentResolver

from ..preparerstep import PreparerStep, PreparerMapping


class Preprocessor(PreparerStep):
    """Apply preprocessing steps to each column.

    Params:
        *args: args to PreparerStep constructor.
        **kwargs: kwargs to PreparerStep constructor.

    """

    # TODO: create column_sharer if not exists in PreparerStep, this is pending
    # Chris's merge so I can take advantage of new core API

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _def_get_mapping(self, X):
        # Add code to auto create column sharer in preparerstep if it is not
        # passed in

        # TODO: This needs to get fixed in a base class
        # ie a baseclass needs to resolve the "cache miss"

        pm = PreparerMapping()
        for i, c in enumerate(X.columns):
            intent = self.column_sharer["intent", c]
            if intent is None:
                IntentResolver(column_sharer=self.column_sharer).fit(X)
                intent = self.column_sharer["intent", c]
            transformers_class_list = config.get_preprocessor_steps(intent)
            if (transformers_class_list is not None) or (
                len(transformers_class_list) > 0
            ):
                transformer_list = [
                    tc()  # TODO: Allow kwargs in config
                    for tc in transformers_class_list
                ]
            else:
                transformer_list = None  # None or []
            pm.add([c], transformer_list)
        return pm

    def get_mapping(self, X):
        """Return the mapping of transformations for the DataCleaner step.

        Args:
            X: input DataFrame.

        Returns:
            Mapping in accordance with super.

        """
        return self._def_get_mapping(X)


# if __name__ == "__main__":
#     from foreshadow.utils.testing import debug
#
#     debug()
#     import numpy as np
#     import pandas as pd
#     from foreshadow.preparer import ColumnSharer
#
#     columns = ["financials"]
#     data = pd.DataFrame({"financials": np.arange(10)}, columns=columns)
#     cs = ColumnSharer()
#     p = Preprocessor(cs)
#     p.fit(data)
#     import pdb
#
#     pdb.set_trace()
