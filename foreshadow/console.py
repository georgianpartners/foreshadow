import argparse
import json
import sys
import warnings

import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import GridSearchCV, train_test_split

from foreshadow import Foreshadow, Preprocessor
from foreshadow.estimators import AutoEstimator
from foreshadow.estimators.auto import determine_problem_type


def generate_model(args):
    """ Takes the arguments passed to the console and generates
    the Foreshadow model that must be fit.
    """

    parser = argparse.ArgumentParser(
        description="Peer into the future of a data science project"
    )
    parser.add_argument(
        "--data", type=str, help="File path of a valid CSV file to load"
    )
    parser.add_argument(
        "--target",
        type=str,
        help="Name of target column to predict in dataset",
    )
    parser.add_argument(
        "--level",
        default=1,
        type=int,
        help="Level of fitting 1: All defaults 2: Feature engineering"
        "parameter search 3: Model parameter search"
        "using AutoSklearn or TPOT ",
    )
    parser.add_argument(
        "--method",
        default=None,
        type=str,
        help="Name of Estimator class from sklearn.linear_model to use."
        "Defaults to LogisticRegression for classification"
        "and LinearRegression for regression",
    )
    parser.add_argument(
        "--time",
        default=10,
        type=int,
        help="Time limit in minutes to apply to model"
        "parameter search. (Default 10)",
    )
    parser.add_argument(
        "--x_config",
        default=None,
        type=str,
        help="Path to JSON configuration file for X Preprocessor",
    )
    parser.add_argument(
        "--y_config",
        default=None,
        type=str,
        help="Path to JSON configuration file for y Preprocessor",
    )
    cargs = parser.parse_args(args)

    if cargs.level == 3 and cargs.method is not None:
        warnings.warn(
            "WARNING: Level 3 model search enabled. Method will be ignored."
        )

    if cargs.level != 3 and cargs.time != 10:
        warnings.warn(
            "WARNING: Time parameter not applicable "
            "to feature engineering. Must be in level 3."
        )

    try:
        df = pd.read_csv(cargs.data)
    except Exception:
        raise ValueError(
            "Failed to load file. Please verify it exists and is a valid CSV."
        )

    try:
        X_df = df.drop(columns=cargs.target)
        y_df = df[[cargs.target]]
    except Exception:
        raise ValueError("Invalid target variable")

    X_train, X_test, y_train, y_test = train_test_split(
        X_df, y_df, test_size=0.2
    )

    if cargs.level == 1:
        # Default everything with basic estimator
        fs = Foreshadow(estimator=get_method(cargs.method, y_train))

    elif cargs.level == 2:
        # Parameter search on all matched intents

        if cargs.x_config is not None:
            try:
                with open(cargs.x_config, "r") as f:
                    X_search = Preprocessor(from_json=json.load(f))
            except Exception:
                raise ValueError(
                    "Could not read X config file {}".format(cargs.x_config)
                )
            print("Reading config for X Preprocessor")
        else:
            X_search = search_intents(X_train)
            print("Searching over valid intent space for X data")

        if cargs.y_config is not None:
            try:
                with open(cargs.y_config, "r") as f:
                    y_search = Preprocessor(from_json=json.load(f))
            except Exception:
                raise ValueError(
                    "Could not read y config file {}".format(cargs.y_config)
                )
            print("Reading config for y Preprocessor")
        else:
            y_search = search_intents(y_train)
            print("Searching over valid intent space for y data")

        # If level 3 also do model parameter search with AutoEstimator
        # Input time limit into Foreshadow to be passed into AutoEstimator

        fs = Foreshadow(
            X_preprocessor=X_search,
            y_preprocessor=y_search,
            estimator=get_method(cargs.method, X_train),
            optimizer=GridSearchCV,
        )

    elif cargs.level == 3:
        # Default intent and advanced model search using 3rd party AutoML

        fs = Foreshadow(
            estimator=AutoEstimator(
                estimator_kwargs={"max_time_mins": cargs.time}
            )
        )

    else:
        raise ValueError("Invalid Level. Levels 1 - 3 supported.")

    return fs, X_train, y_train, X_test, y_test


def execute_model(fs, X_train, y_train, X_test, y_test):
    """ Executes the model produced by generate_model()
    and exports the data to json as well as returning the
    exported json object containing the results and the serialized
    Foreshadow object. Also prints simple model accuracy metrics.
    """

    print("Fitting final model...")
    fs.fit(X_train, y_train)

    print("Scoring final model...")
    score = fs.score(X_test, y_test)

    print("Final Results: ")
    print(score)

    # Store final results
    all_results = {
        "X_Model": fs.X_preprocessor.serialize(),
        "X_Summary": fs.X_preprocessor.summarize(X_train),
        "y_Model": fs.y_preprocessor.serialize(),
        "y_summary": fs.y_preprocessor.summarize(y_train),
    }

    with open("model.json", "w") as outfile:
        json.dump(all_results, outfile)

    print(
        "Results of model fiting have been saved to model.json."
        "Refer to docs to read and process."
    )

    return all_results


def cmd():  # pragma: no cover
    """ Entry point to foreshadow via console command. Uncovered as
    this function only serves to be executed manually.
    """

    model = generate_model(sys.argv[1:])
    execute_model(*model)


def get_method(arg, y_train):
    """ Function to determine what estimator to use given a set of X data
    and a passed argument referencing an sklearn Estimator class.
    """

    if arg is not None:
        try:
            mod = __import__(
                "sklearn.linear_model", globals(), locals(), ["object"], 0
            )
            cls = getattr(mod, arg)
            return cls()
        except Exception:
            raise ValueError(
                "Invalid method. {} is not a valid "
                "estimator from sklearn.linear_model".format(arg)
            )

    else:
        return (
            LinearRegression()
            if determine_problem_type(y_train) == "regression"
            else LogisticRegression()
        )


def search_intents(data):

    proc = Preprocessor()

    proc.fit(data)

    result = proc.serialize()

    space = {
        "columns": {
            k: {"intent": v["intent"]} for k, v in result["columns"].items()
        },
        "combinations": [
            {
                "columns.{}.intent".format(k): v["all_matched_intents"]
                for k, v in result["columns"].items()
            }
        ],
    }

    return Preprocessor(from_json=space)
