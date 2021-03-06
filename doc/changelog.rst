.. _changelog:

.. towncrier release notes start

Foreshadow 1.0.0 (2020-03-20)
=============================

Features
--------

- AutoIntent Resolving Dependency upgrade
    The automl intent resolving model has now been retrained with pandas 0.25 and sklearn 0.22 (autointent-resolving-dependency-upgrade)
- Adding support for Text Intent and Text transformation pipeline
    Foreshadow now supports Text Intent and has a pipeline processing Text using TFIDF and TruncatedSVD. (text-transformation-pipeline)


Foreshadow 0.4.5 (2020-03-09)
=============================

Features
--------

- Dependency upgrade and related code changes
    Scikit-Learn 0.19 -> 0.22.1
    Pandas 0.23 -> 0.25

    Removed ParallelProcessor and DynamicPipeline in favor of native ColumnTransformer. (dependency-upgrade)


Foreshadow 0.4.4 (2020-01-29)
=============================

Features
--------

- Bug fixes and updates:
    1. AutoIntent Resolving code update.
    2. fixing intent override from Categorical to Numeric issue in DataExportor. (bug-fixes)


Foreshadow 0.4.3 (2020-01-08)
=============================

Features
--------

- Bug fixes and updates:
    1. Fix an issue in exported pickle file missing label encoder for target
  variabes.
    2. [Experimental] Allow user to supply customized cleaning functions. (bug-fixes-and-updates)


Foreshadow 0.4.2 (2019-12-23)
=============================

Features
--------

- Bug fixes and updates:
    1. Add drop functionality to the transform method in the cleaner mapper. (bug-fix-4)


Foreshadow 0.4.1 (2019-12-23)
=============================

Features
--------

- Bug fixes and updates:
    1. Abort the training process is the whole dataframe is empty due to
  missing data after data cleaning step. (bug-fix-3)


Foreshadow 0.4.0 (2019-12-20)
=============================

Features
--------

- Bug fixes and updates:
    1. Allow user to pickle fitted_pipeline.
    2. Treat NaN as a category.
    3. Runtime performance improving with data sampling on cleaning and intent
  resolving steps.
    4. Export processed dataset before fitting the estimator.
    5. Disable dummy encoding in categorical encoding process temporarily. (bug-fix-2)


Foreshadow 0.3.2 (2019-12-03)
=============================

Features
--------

- Feature: Bug fix for intent override
    Add back the missing intent override (bug-fix-for-intent-override)


Foreshadow 0.3.0 (2019-11-21)
=============================

Features
--------

- Feature: Auto Intent Resolving
    Automatically resolve the intent of a column with a machine learning model. (auto-intent-resolving)
- Bug fix of pick_transformer may transform dataframe in place, causing
  inconsistency between the data and intended downstream logic. (bug-fix)
- Feature: Enable logging on Foreshadow
    This feature allows Foreshadow to display the progress of the training. (enable-logging)
- Feature: Adding more default models in Foreshadow
    This allows user to select estimators from the following categories:
    - Linear
    - SVM
    - RandomForest
    - NeuralNetwork (more-default-model)
- Feature: Allow user to override intent resolving decisions
    This feature allows users to override the intent resolving decisions
    through API calls. It can be done both before and after fitting the
    foreshadow object. (user-override)


Foreshadow 0.2.1 (2019-09-26)
=============================

Features
--------

- Bug fix of pick_transformer may transform dataframe in place, causing
  inconsistency between the data and intended downstream logic. (bug-fix)


Foreshadow 0.2.0 (2019-09-24)
=============================

Features
--------

- Add feature_summarizer to produce statistics about the data after
  intent resolving to show the users why such decisions are made. (data-summarization)
- Foreshadow is able to run end-to-end with level 1 optimization with the tpot
  auto-estimator. (level1-optimization)
- Add Feature Reducer as a passthrough transformation step. (pass-through-feature-reducer)
- Multiprocessing:
  1. Enable multiprocessing on the dataset.
  2. Collect changes from each process and update the original columnsharer. (process-safe-columnsharer)
- Serialization and deserialization:
  1. Serialization of the foreshadow object in a non-verbose format.
  2. Deserialization of the foreshadow object. (serialization)
- Adding two major components:
  1. usage of metrics for any statistic computation
  2. changing functionality of wrapping sklearn transformers to give them DataFrame capabilities. This now uses classes and metaclasses, which should be easier to maintain (#74)
- Adding ColumnSharer, a lightweight wrapper for a dictionary that functions
  as a cache system, to be used to pass information in the foreshadow pipeline. (#79)
- Creating DataPreparer to handle data preprocessing. Data Cleaning is the
  first step in this process. (#93)
- Adds skip resolve functionality to SmartTransformer, restructure utils, and add is_wrapped to utils (#95)
- Add serializer mixin and resture package import locations. (#96)
- Add configuration file parser. (#99)
- Add Feature Engineerer as a passthrough transformation step. (#112)
- Add Intent Mapper and Metric wrapper features. (#113)
- Add Preprocessor step to DataPreparer (#118)
- Create V2 architecture shift. (#162)


Foreshadow 0.1.0 (2019-06-28)
=============================

Features
--------

- Initial release. (#71)
