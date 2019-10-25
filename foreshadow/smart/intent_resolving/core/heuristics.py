"""Functions to generate metafeatures using heuristics."""

import re

import pandas as pd
from pandas.api import types


def _raise_if_not_pd_series(obj):
    if not isinstance(obj, pd.Series):
        raise TypeError(
            f"Expecting `pd.Series type as input, instead of {type(obj)} type."
        )


def convert_to_numeric(series: pd.Series) -> pd.Series:
    """Retain and convert any numeric data points."""
    return pd.to_numeric(series.copy(), errors="coerce").dropna()


def is_number_as_string(
    series: pd.Series, shrinkage_threshold: float = 0.5
) -> bool:
    """
    Check if string can be numerical.

    Remove non-numerals from string and calculate relative reduction in string length.

    shrinkage_threshold:
        Numeric-like values that are extractable downstream
        should have lengths below this value post-numeral removal.

    Returns:
        True if at least half of the values' relative post-shrinkage length is
        at least `shrinkage_threshold`, and there is at least one value remaining
        after numerical conversion.
    """
    series = series.copy().astype(str)
    nums_removed = series.apply(lambda x: re.sub(r"\D", "", x))
    rel_post_shrinkage_len = nums_removed.apply(len) / series.apply(len)

    most_values_contain_numbers = (
        (rel_post_shrinkage_len > shrinkage_threshold).sum()
        / len(rel_post_shrinkage_len)
    ) >= 0.5

    at_least_one_value_remaining = bool(len(convert_to_numeric(series)))

    return most_values_contain_numbers and at_least_one_value_remaining


def castable_as_numeric(series: pd.Series, threshold: float = 0.95) -> bool:
    """
    Check if series values can be casted as numeric dtypes.

    Returns:
        True if at least `threshold` values can be casted as numerics.
    """
    # Columns which are already of numeric dtype are considered not castable
    if series.dtype in ["float", "int"]:
        return False

    return (len(convert_to_numeric(series)) / len(series)) >= threshold


def numeric_extractable(series: pd.Series, threshold: float = 0.95) -> bool:
    """
    Check if numbers can be extracted from series values.

    Returns:
        True if at least `threshold` values contain numerics.
    """
    # Columns which are already of numeric dtype are considered not extractable
    if series.dtype in ["float", "int"]:
        return False

    series = series.copy().dropna().astype(str)
    n_contains_digits = series.apply(
        lambda x: any(char.isdigit() for char in x)
    ).sum()

    return (n_contains_digits / len(series)) >= threshold


def normalized_distinct_rate(df: pd.DataFrame) -> pd.Series:
    """
    Calculate the % of distinct values relative to the number of non-null entries.

    Arguments:
        df {pd.DataFrame} -- Dataframe to analzye.

    Returns:
        pd.Series -- Normalized distinct rate.
    """
    return df["num_distincts"] / (df["total_val"] - df["num_nans"])


def nan_rate(df: pd.DataFrame) -> pd.Series:
    """
    Calculate the % of NaNs relative to the total number of data points.

    Arguments:
        df {pd.DataFrame} -- Dataframe to analyze.

    Returns:
        pd.Series -- NaN rate.
    """
    return df["num_nans"] / df["total_val"]


def avg_val_len(raw: pd.DataFrame) -> pd.Series:
    """
    Get the average length values in the feature column.

    Returns -1 if feature column is completely empty.

    Arguments:
        raw {pd.DataFrame} -- Raw dataframe to analyze.

    Returns:
        pd.Series -- [description]
    """
    result = []
    for col in raw:
        series = raw[col].dropna()

        if not len(series):
            result.append(-1)
            continue

        result.append(sum(len(str(x)) for x in series) / len(series))

    return pd.Series(result, index=raw.columns)


def maybe_zipcode(raw: pd.DataFrame, threshold: float = 0.95) -> pd.Series:
    """
    Infer if DataFrame might be a zipcode.

    The three decision criteria are:
    1. 'zip' appears in the name
    2. At least `threshold` values look like US zipcodes (5 digits).
    3. At least `threshold` values look like Canadian zipcodes (*#* #*#).

    Arguments:
        raw {pd.DataFrame} -- Raw pd.Series to analyze.

    Keyword Arguments:
        threshold {float} -- Minimum value for criterion to be considered met. (default: {0.95})

    Returns:
        pd.Series[int] -- Scores for each series in dataframe.
                          A point is given for each criterion met.
    """
    return raw.apply(_maybe_zipcode)


def _maybe_zipcode(raw_s: pd.Series, threshold: float = 0.95) -> int:
    """
    Infer if series might be a zipcode.

    The three decision criteria are:
    1. 'zip' appears in the name
    2. At least `threshold` values look like US zipcodes (5 digits).
    3. At least `threshold` values look like Canadian zipcodes (*#* #*#).

    Arguments:
        raw_s {pd.Series} -- Raw pd.Series to analyze.

    Keyword Arguments:
        threshold {float} -- Minimum value for criterion to be considered met. (default: {0.95})

    Returns:
        int -- Score. A point is given for each criterion met.
    """
    _raise_if_not_pd_series(raw_s)

    points = 0

    # Criterion 1
    if "zip" in str(raw_s.name):
        points += 1

    # Criterion 2
    at_least_5_digits = raw_s.apply(
        lambda x: len(str(x)) == 5 and str(x).isnumeric()
    )
    if (at_least_5_digits.sum() / len(raw_s)) >= threshold:
        points += 1

    # Criterion 3
    is_cad_zip = raw_s.apply(
        lambda x: bool(re.search(r"\w\d\w\s?\d\w\d", str(x)))
    )
    if (is_cad_zip.sum() / len(raw_s)) >= threshold:
        points += 1

    return points


def maybe_real_as_enum(
    df: pd.DataFrame, max_n_distinct: int = 20
) -> pd.Series:
    """
    Evaluate if feature column might be categorical.

    Check that values are numeric and at most `max_n_distinct` distinct values.

    Arguments:
        df {pd.DataFrame} -- Metafeatures.

    Keyword Arguments:
        max_n_distinct {int} -- Maximum number of default categories. (default: {20})

    Returns:
        pd.Series -- A boolean series on whether a model might be categorical or not.
    """
    sample_columns = [col for col in df.columns if "sample" in col]

    is_numeric = [
        types.is_numeric_dtype(df[sample_columns].iloc[i])
        for i in range(len(df))
    ]
    limited_distinct_values = df["num_distincts"] <= max_n_distinct

    return is_numeric & limited_distinct_values


def is_int_dtype(df: pd.DataFrame) -> pd.Series:
    """
    Check if each series in DataFrame is of an integer dtype.

    Wrapper function to allow function to be applied on the entire dataframe
    instead of a series level. This is a workaround to dill which fails to pickle
    local contexts in nested lambda statements.
    """
    return df.apply(lambda s: types.is_integer_dtype(s), result_type="expand")


def is_float_dtype(df: pd.DataFrame) -> pd.Series:
    """
    Check if each series in DataFrame is of a float dtype.

    Wrapper function to allow function to be applied on the entire dataframe
    instead of a series level. This is a workaround to dill which fails to pickle
    local contexts in nested lambda statements.
    """
    return df.apply(lambda s: types.is_float_dtype(s), result_type="expand")


def is_bool_dtype(df: pd.DataFrame) -> pd.Series:
    """
    Check if each series in DataFrame is of a bool dtype.

    Wrapper function to allow function to be applied on the entire dataframe
    instead of a series level. This is a workaround to dill which fails to pickle
    local contexts in nested lambda statements.
    """
    return df.apply(lambda s: types.is_bool_dtype(s), result_type="expand")


def is_string_dtype(df: pd.DataFrame) -> pd.Series:
    """
    Check if each series in DataFrame is of a string dtype.

    Wrapper function to allow function to be applied on the entire dataframe
    instead of a series level. This is a workaround to dill which fails to pickle
    local contexts in nested lambda statements.
    """
    return df.apply(lambda s: types.is_string_dtype(s), result_type="expand")


def is_datetime_dtype(df: pd.DataFrame) -> pd.Series:
    """
    Check if each series in DataFrame is of a datetime dtype.

    Wrapper function to allow function to be applied on the entire dataframe
    instead of a series level. This is a workaround to dill which fails to pickle
    local contexts in nested lambda statements.
    """
    return df.apply(
        lambda s: types.is_datetime64_any_dtype(s), result_type="expand"
    )


def is_timedelta_dtype(df: pd.DataFrame) -> pd.Series:
    """
    Check if each series in DataFrame is of a timedelta dtype.

    Wrapper function to allow function to be applied on the entire dataframe
    instead of a series level. This is a workaround to dill which fails to pickle
    local contexts in nested lambda statements.
    """
    return df.apply(
        lambda s: types.is_timedelta64_dtype(s), result_type="expand"
    )


def is_category_dtype(df: pd.DataFrame) -> pd.Series:
    """
    Check if each series in DataFrame is of a categorical dtype.

    Wrapper function to allow function to be applied on the entire dataframe
    instead of a series level. This is a workaround to dill which fails to pickle
    local contexts in nested lambda statements.
    """
    return df.apply(
        lambda s: types.is_categorical_dtype(s), result_type="expand"
    )


def sample_sets(raw: pd.DataFrame) -> pd.Series:
    """
    Get the samples set.

    Arguments:
        raw {pd.DataFrame} -- Raw dataframe to analyze.

    Returns:
        pd.Series -- A series of unique sets for each feature column.
    """
    return raw.apply(lambda s: set(s.dropna().unique()))
