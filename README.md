# The effects of mismatched train and test data cleaning pipelines on regression models: lessons for practice

This repository contains both the code used for performing the experiments in 'The effects of mismatched train and test data cleaning pipelines on regression models: lessons for practice' and supplementary material for recreating the analysis. The supplementary material includes the appendix and CSV files containing the main results, as well as  the Jupyter notebooks for analysing these results.

## Code

Running the experiment code makes use of the following packages and version numbers:

- numpy=1.23.5
- pandas=1.5.2
- scikit-learn=1.3.2
- scipy=1.9.3
- multiprocess=0.70.12.2
- xgboost=2.0.0
- joblib=1.3.2

The experiments for a given dataset (Airbnb or USCensus) can be reproduced as follows:
1. Create the cleaned training and test data splits using the '*dataset*_data_cleaning' Jupyter notebook.
2. Train the different models on the cleaned training data using the '*dataset*_model_fitting' Jupyter notebook.
3. Test the trained models on the different cleaned test data using the '*dataset*_model_inference' Jupyter notebook.

## Analysis

Running the analysis makes use of the following packages and version numbers, in addition to the pandas and numpy libraries above:

- seaborn=0.12.2
- matplotlib=3.6.2

The analysis on model performance and variable distributions can be performed using the 'model_results_analysis' and 'cleaning_effects_airbnb' Jupyter notebooks in the 'supplementary material' folder.
