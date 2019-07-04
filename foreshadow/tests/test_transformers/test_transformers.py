import pytest


def test_transformer_wrapper_init():
    from foreshadow.transformers.externals import StandardScaler

    scaler = StandardScaler(name="test-scaler", keep_columns=True)

    assert scaler.name == "test-scaler"
    assert scaler.keep_columns is True


def test_transformer_wrapper_no_init():
    from sklearn.base import BaseEstimator, TransformerMixin
    from foreshadow.transformers.transformers import make_pandas_transformer

    class NewTransformer(BaseEstimator, TransformerMixin):
        pass

    trans = make_pandas_transformer(NewTransformer)
    _ = trans()

    assert hasattr(trans.__init__, "__defaults__")


def test_transformer_wrapper_function():
    import os

    import numpy as np
    import pandas as pd
    from sklearn.preprocessing import StandardScaler as StandardScaler
    from foreshadow.transformers.externals import (
        StandardScaler as CustomScaler,
    )

    boston_path = os.path.join(
        os.path.dirname(__file__), "..", "test_data", "boston_housing.csv"
    )

    df = pd.read_csv(boston_path)

    custom = CustomScaler()
    sklearn = StandardScaler()

    custom.fit(df[["crim"]])
    sklearn.fit(df[["crim"]])

    custom_tf = custom.transform(df[["crim"]])
    sklearn_tf = sklearn.transform(df[["crim"]])

    assert np.array_equal(custom_tf.values, sklearn_tf)

    custom_tf = custom.fit_transform(df[["crim"]])
    sklearn_tf = sklearn.fit_transform(df[["crim"]])

    assert np.array_equal(custom_tf.values, sklearn_tf)


def test_transformer_wrapper_empty_input():
    import numpy as np
    import pandas as pd

    from sklearn.preprocessing import StandardScaler as StandardScaler
    from foreshadow.transformers.externals import (
        StandardScaler as CustomScaler,
    )

    df = pd.DataFrame({"A": np.array([])})
    print(df.empty)

    with pytest.raises(ValueError) as e:
        StandardScaler().fit(df)
    cs = CustomScaler().fit(df)
    out = cs.transform(df)

    assert "Found array with" in str(e)
    assert out.values.size == 0

    # If for some weird reason transform is called before fit
    assert CustomScaler().transform(df).values.size == 0


def test_transformer_keep_cols():
    import os

    import pandas as pd
    from foreshadow.transformers.externals import (
        StandardScaler as CustomScaler,
    )

    boston_path = os.path.join(
        os.path.dirname(__file__), "..", "test_data", "boston_housing.csv"
    )

    df = pd.read_csv(boston_path)

    custom = CustomScaler(keep_columns=True)
    custom_tf = custom.fit_transform(df[["crim"]])

    assert custom_tf.shape[1] == 2


def test_transformer_naming_override():
    import os

    from foreshadow.transformers.externals import StandardScaler
    import pandas as pd

    boston_path = os.path.join(
        os.path.dirname(__file__), "..", "test_data", "boston_housing.csv"
    )

    df = pd.read_csv(boston_path)

    scaler = StandardScaler(name="test", keep_columns=False)
    out = scaler.fit_transform(df[["crim"]])

    assert out.iloc[:, 0].name == "crim_test_0"


def test_transformer_naming_default():
    import os

    from foreshadow.transformers.externals import StandardScaler
    import pandas as pd

    boston_path = os.path.join(
        os.path.dirname(__file__), "..", "test_data", "boston_housing.csv"
    )

    df = pd.read_csv(boston_path)

    scaler = StandardScaler(keep_columns=False)
    out = scaler.fit_transform(df[["crim"]])

    assert out.iloc[:, 0].name == "crim_StandardScaler_0"


def test_transformer_parallel_invalid():
    from foreshadow.transformers.base import ParallelProcessor

    class InvalidTransformer:
        pass

    t = InvalidTransformer()

    with pytest.raises(TypeError) as e:
        ParallelProcessor([("scaled", t, ["crim", "zn", "indus"])])

    assert str(e.value) == (
        "All estimators should implement fit and "
        "transform. '{}'"
        " (type {}) doesn't".format(t, type(t))
    )


def test_transformer_parallel_empty():
    import os

    import pandas as pd
    from foreshadow.transformers.base import ParallelProcessor

    boston_path = os.path.join(
        os.path.dirname(__file__), "..", "test_data", "boston_housing.csv"
    )

    df = pd.read_csv(boston_path)

    proc = ParallelProcessor(
        [
            (
                "scaled",
                ParallelProcessor([("cscale", None, ["crim"])]),
                ["crim", "zn", "indus"],
            )
        ]
    )

    proc.fit(df[[]])
    tf = proc.transform(df[[]])

    assert tf.equals(df[[]])

    tf = proc.fit_transform(df[[]])

    assert tf.equals(df[[]])


def test_transformer_parallel():
    import os

    import pandas as pd

    from foreshadow.transformers.base import ParallelProcessor
    from foreshadow.transformers.externals import StandardScaler

    boston_path = os.path.join(
        os.path.dirname(__file__), "..", "test_data", "boston_housing.csv"
    )

    df = pd.read_csv(boston_path)

    ss = StandardScaler(name="scaled")

    proc = ParallelProcessor(
        [
            (
                "scaled",
                StandardScaler(keep_columns=False),
                ["crim", "zn", "indus"],
            )
        ],
        collapse_index=True,
    )

    ss.fit(df[["crim", "zn", "indus"]])
    proc.fit(df)

    tf = proc.transform(df)
    tf_2 = proc.fit_transform(df)

    assert tf.equals(tf_2)

    tf_norm = ss.transform(df[["crim", "zn", "indus"]])
    tf_others = df.drop(["crim", "zn", "indus"], axis=1)
    tf_test = pd.concat([tf_norm, tf_others], axis=1)
    tf_test.columns = tf_test.columns.rename("new")

    tf.sort_values("new", axis=1, inplace=True)
    tf_test.sort_values("new", axis=1, inplace=True)

    assert tf.equals(tf_test)


def test_transformer_pipeline():
    import os

    import pandas as pd
    import numpy as np

    np.random.seed(1337)

    from foreshadow.transformers.externals import (
        StandardScaler as CustomScaler,
    )
    from foreshadow.transformers.base import ParallelProcessor

    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import FeatureUnion

    from sklearn.pipeline import Pipeline
    from sklearn.linear_model import LinearRegression

    boston_path = os.path.join(
        os.path.dirname(__file__), "..", "test_data", "boston_housing.csv"
    )

    df = pd.read_csv(boston_path)

    target = df["medv"]
    df = df[["crim", "zn", "indus"]]
    test = df.copy(deep=True)

    custom = Pipeline(
        [
            (
                "Step1",
                ParallelProcessor(
                    [
                        (
                            "scaled",
                            CustomScaler(keep_columns=False),
                            ["crim", "zn", "indus"],
                        )
                    ]
                ),
            ),
            ("estimator", LinearRegression()),
        ]
    )

    sklearn = Pipeline(
        [
            ("Step1", FeatureUnion([("scaled", StandardScaler())])),
            ("estimator", LinearRegression()),
        ]
    )

    sklearn.fit(df, target)
    custom.fit(df, target)

    assert np.array_equal(custom.predict(test), sklearn.predict(test))


def test_smarttransformer_notimplemented():
    import os

    import pandas as pd

    from foreshadow.transformers.base import SmartTransformer

    boston_path = os.path.join(
        os.path.dirname(__file__), "..", "test_data", "boston_housing.csv"
    )

    df = pd.read_csv(boston_path)

    class TestSmartTransformer(SmartTransformer):
        pass

    transformer = TestSmartTransformer()

    with pytest.raises(NotImplementedError) as e:
        transformer.fit(df[["crim"]])

    assert (
        str(e.value) == "WrappedTransformer _get_transformer was not "
        "implimented."
    )


def test_smarttransformer_attributeerror():
    import os

    import pandas as pd

    from foreshadow.transformers.base import SmartTransformer

    boston_path = os.path.join(
        os.path.dirname(__file__), "..", "test_data", "boston_housing.csv"
    )

    df = pd.read_csv(boston_path)

    class TestSmartTransformer(SmartTransformer):
        def _get_transformer(self, X, y=None, **fit_params):
            return "INVALID"

    transformer = TestSmartTransformer()

    with pytest.raises(AttributeError) as e:
        transformer.fit(df[["crim"]])

    assert (
        str(e.value) == "Invalid WrappedTransformer. Get transformer "
        "returns invalid object"
    )


def test_smarttransformer_invalidtransformer():
    import os

    import pandas as pd

    from foreshadow.transformers.base import SmartTransformer

    boston_path = os.path.join(
        os.path.dirname(__file__), "..", "test_data", "boston_housing.csv"
    )

    df = pd.read_csv(boston_path)

    class InvalidClass:
        pass

    class TestSmartTransformer(SmartTransformer):
        def _get_transformer(self, X, y=None, **fit_params):
            return InvalidClass()

    transformer = TestSmartTransformer()

    with pytest.raises(AttributeError) as e:
        transformer.fit(df[["crim"]])

    assert (
        str(e.value) == "Invalid WrappedTransformer. Get transformer "
        "returns invalid object"
    )


def test_smarttransformer_function():
    import os

    import pandas as pd

    from foreshadow.transformers.base import SmartTransformer
    from foreshadow.transformers.externals import StandardScaler

    boston_path = os.path.join(
        os.path.dirname(__file__), "..", "test_data", "boston_housing.csv"
    )

    df = pd.read_csv(boston_path)

    class TestSmartTransformer(SmartTransformer):
        def _get_transformer(self, X, y=None, **fit_params):
            return StandardScaler()

    smart = TestSmartTransformer()
    smart_data = smart.fit_transform(df[["crim"]])

    std = StandardScaler()
    std_data = std.fit_transform(df[["crim"]])

    assert smart_data.equals(std_data)

    smart.fit(df[["crim"]])
    smart_data = smart.transform(df[["crim"]])

    std.fit(df[["crim"]])
    std_data = std.transform(df[["crim"]])

    assert smart_data.equals(std_data)


def test_smarttransformer_function_override():
    import os

    import pandas as pd

    from foreshadow.transformers.base import SmartTransformer
    from foreshadow.transformers.externals import Imputer

    boston_path = os.path.join(
        os.path.dirname(__file__), "..", "test_data", "boston_housing.csv"
    )

    df = pd.read_csv(boston_path)

    class TestSmartTransformer(SmartTransformer):
        pass

    smart = TestSmartTransformer(override="Imputer", name="impute")
    smart_data = smart.fit_transform(df[["crim"]])

    assert smart.transformer.name == "impute"

    std = Imputer(name="impute")
    std_data = std.fit_transform(df[["crim"]])

    assert smart_data.equals(std_data)

    smart.fit(df[["crim"]])
    smart_data = smart.transform(df[["crim"]])

    std.fit(df[["crim"]])
    std_data = std.transform(df[["crim"]])

    assert smart_data.equals(std_data)


def test_smarttransformer_function_override_invalid():
    from foreshadow.transformers.base import SmartTransformer

    class TestSmartTransformer(SmartTransformer):
        pass

    smart = TestSmartTransformer(override="BAD")

    with pytest.raises(ValueError) as e:
        smart.fit([1, 2, 3])

    assert str(e.value) == "Could not import defined transformer BAD"


def test_smarttransformer_set_params_override():
    from foreshadow.transformers.base import SmartTransformer
    from foreshadow.transformers.externals import StandardScaler

    class TestSmartTransformer(SmartTransformer):
        pass

    smart = TestSmartTransformer(override="Imputer")
    smart.set_params(**{"override": "StandardScaler"})

    assert isinstance(smart.transformer, StandardScaler)


def test_smarttransformer_set_params_empty():
    from foreshadow.transformers.base import SmartTransformer

    class TestSmartTransformer(SmartTransformer):
        pass

    smart = TestSmartTransformer()
    smart.set_params()

    assert smart._transformer is None


def test_smarttransformer_null_transformer():
    from foreshadow.transformers.base import SmartTransformer

    class TestSmartTransformer(SmartTransformer):
        pass

    smart = TestSmartTransformer()

    with pytest.raises(ValueError) as e:
        smart.transformer

    assert str(e.value) == "Smart Transformer not Fit"


def test_smarttransformer_set_params_default():
    from foreshadow.transformers.base import SmartTransformer
    from foreshadow.transformers.externals import StandardScaler

    class TestSmartTransformer(SmartTransformer):
        def _get_transformer(self, X, y=None, **fit_params):
            return StandardScaler()

    smart = TestSmartTransformer()
    smart.fit([1, 2, 3])

    smart.set_params(**{"transformer__with_mean": False})

    assert not smart.transformer.with_mean


def test_smarttransformer_get_params():
    from foreshadow.transformers.base import SmartTransformer

    class TestSmartTransformer(SmartTransformer):
        pass

    smart = TestSmartTransformer(
        override="Imputer", missing_values="NaN", strategy="mean"
    )
    smart.fit([1, 2, 3])

    params = smart.get_params()

    assert params == {
        "override": "Imputer",
        "name": None,
        "keep_columns": False,
        "axis": 0,
        "copy": True,
        "missing_values": "NaN",
        "strategy": "mean",
        "verbose": 0,
        "y_var": False,
    }


def test_smarttransformer_empty_inverse():
    from foreshadow.transformers.base import SmartTransformer

    class TestSmartTransformer(SmartTransformer):
        def _get_transformer(self, X, y=None, **fit_params):
            return None

    smart = TestSmartTransformer()
    smart.fit([])

    assert smart.inverse_transform([1, 2, 10]).size == 0


def test_sparse_matrix_conversion():
    from foreshadow.transformers.internals import FixedTfidfVectorizer

    corpus = [
        "Hello world!",
        "It's a small world.",
        "Small, incremental steps make progress",
    ]

    tfidf = FixedTfidfVectorizer()

    # This tf generates sparse output by default and if not handled will
    # break pandas wrapper
    tfidf.fit_transform(corpus)


@pytest.mark.parametrize(
    "transformer,input_csv",
    [
        ("StandardScaler", "./foreshadow/tests/test_data/boston_housing.csv"),
        ("OneHotEncoder", "./foreshadow/tests/test_data/boston_housing.csv"),
        (
            "TfidfTransformer",
            "./foreshadow/tests/test_data/boston_housing.csv",
        ),
    ],
)
def test_make_pandas_transformer_fit(transformer, input_csv):
    """Test make_pandas_transformer has initial transformer fit functionality.

        Args:
            transformer: wrapped transformer
            input_csv: dataset to test on

    """
    from importlib import import_module
    import pandas as pd

    mod = import_module("foreshadow.transformers.externals")
    transformer = getattr(mod, transformer)()
    df = pd.read_csv(input_csv)
    assert transformer.fit(df) == transformer


@pytest.mark.parametrize(
    "transformer,expected_path",
    [
        ("StandardScaler", "sklearn.preprocessing"),
        ("OneHotEncoder", "category_encoders"),
        ("TfidfTransformer", "sklearn.feature_extraction.text"),
    ],
)
def test_make_pandas_transformer_meta(transformer, expected_path):
    """Test that the wrapped transformer has proper metadata.

    Args:
        transformer: wrapped transformer
        expected_path: path to the initial transformer

    Returns:

    """
    from importlib import import_module

    mod = import_module(expected_path)
    expected = getattr(mod, transformer)
    mod = import_module("foreshadow.transformers.externals")
    transformer = getattr(mod, transformer)()
    assert isinstance(transformer, expected)  # should remain a subclass
    assert type(transformer).__name__ == expected.__name__
    assert transformer.__doc__ == expected.__doc__


@pytest.mark.parametrize(
    "transformer,kwargs,sk_path,input_csv",
    [
        (
            "StandardScaler",
            {},
            "sklearn.preprocessing",
            "./foreshadow/tests/test_data/boston_housing.csv",
        ),
        (
            "OneHotEncoder",
            {},
            "category_encoders",
            "./foreshadow/tests/test_data/boston_housing.csv",
        ),
        (
            "TfidfTransformer",
            {},
            "sklearn.feature_extraction.text",
            "./foreshadow/tests/test_data/boston_housing.csv",
        ),
    ],
)
def test_make_pandas_transformer_transform(
    transformer, kwargs, sk_path, input_csv
):
    """Test wrapped transformer has the initial transform functionality.

        Args:
            transformer: wrapped transformer
            kwargs: key word arguments for transformer initialization
            sk_path: path to the module containing the wrapped sklearn
                transformer
            input_csv: dataset to test on

    """
    from importlib import import_module
    import pandas as pd
    import numpy as np
    from scipy.sparse import issparse

    sk_mod = import_module(sk_path)
    sk_transformer = getattr(sk_mod, transformer)(**kwargs)
    mod = import_module("foreshadow.transformers.externals")
    transformer = getattr(mod, transformer)(**kwargs)
    df = pd.read_csv(input_csv)
    crim_df = df[["crim"]]
    transformer.fit(crim_df)
    sk_transformer.fit(crim_df)
    sk_out = sk_transformer.transform(crim_df)
    if issparse(sk_out):
        sk_out = sk_out.toarray()
    assert np.array_equal(transformer.transform(crim_df).values, sk_out)


@pytest.mark.parametrize(
    "transformer,sk_path,input_csv",
    [
        (
            "StandardScaler",
            "sklearn.preprocessing",
            "./foreshadow/tests/test_data/boston_housing.csv",
        ),
        (
            "TfidfTransformer",
            "sklearn.feature_extraction.text",
            "./foreshadow/tests/test_data/boston_housing.csv",
        ),
    ],
)
def test_make_pandas_transformer_fit_transform(
    transformer, sk_path, input_csv
):
    """Test wrapped transformer has initial fit_transform functionality.

        Args:
            transformer: wrapped transformer
            sk_path: path to the module containing the wrapped sklearn
                transformer
            input_csv: dataset to test on

    """
    from importlib import import_module
    import pandas as pd
    import numpy as np
    from scipy.sparse import issparse

    sk_mod = import_module(sk_path)
    sk_transformer = getattr(sk_mod, transformer)()
    mod = import_module("foreshadow.transformers.externals")
    transformer = getattr(mod, transformer)()
    df = pd.read_csv(input_csv)
    crim_df = df[["crim"]]
    sk_out = sk_transformer.fit_transform(crim_df)
    if issparse(sk_out):
        sk_out = sk_out.toarray()
    assert np.array_equal(transformer.fit_transform(crim_df).values, sk_out)


@pytest.mark.parametrize(
    "transformer,sk_path",
    [
        ("StandardScaler", "sklearn.preprocessing"),
        ("TfidfTransformer", "sklearn.feature_extraction.text"),
    ],
)
def test_make_pandas_transformer_init(transformer, sk_path):
    """Test make_pandas_transformer has initial transformer init functionality.

    Should be able to accept any parameters from the sklearn transformer and
    initialize on the wrapped instance.

        Args:
            transformer: wrapped transformer
            sk_path: path to the module containing the wrapped sklearn
                transformer
    """
    from importlib import import_module

    sk_mod = import_module(sk_path)
    sk_transformer = getattr(sk_mod, transformer)()
    params = sk_transformer.get_params()
    mod = import_module("foreshadow.transformers.externals")
    getattr(mod, transformer)(**params)
