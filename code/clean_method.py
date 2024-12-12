# define the domain of cleaning method
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import sys
#import utils
import os

class MVCleaner(object):
    def __init__(self, method='delete', **kwargs):
        self.method = method
        self.kwargs = kwargs
        self.is_fit = False
        if method == 'impute':
            if 'num' not in kwargs or 'cat' not in kwargs:
                print("Must give imputation method for numerical and categorical data")
                sys.exit(1)
            self.tag = "impute_{}_{}".format(kwargs['num'], kwargs['cat'])
        else:
            self.tag = "delete"

    def detect(self, df):
        return df.isnull()

    def fit(self, df):
        if self.method == 'impute':
            num_method = self.kwargs['num']
            cat_method = self.kwargs['cat']
            num_df = df.select_dtypes(include='number')
            cat_df = df.select_dtypes(exclude='number')
            if num_method == "mean":
                num_imp = num_df.mean(numeric_only=True)
            if num_method == "median":
                num_imp = num_df.median()
            if num_method == "mode":
                num_imp = num_df.mode().iloc[0]

            if cat_method == "mode":
                cat_imp = cat_df.mode().iloc[0]
            if cat_method == "dummy":
                cat_imp = ['missing'] * len(cat_df.columns)
                cat_imp = pd.Series(cat_imp, index=cat_df.columns)
            self.impute = pd.concat([num_imp, cat_imp], axis=0)
        self.is_fit = True

    def repair(self, df):
        if self.method == 'delete':
            df_clean = df.dropna()

        if self.method == 'impute':
            df_clean = df.fillna(value=self.impute)
        return df_clean

    def clean_df(self, df):
        if not self.is_fit:
            print('Must fit before clean.')
            sys.exit()
        mv_mat = self.detect(df)
        df_clean = self.repair(df)
        return df_clean, mv_mat

    def clean(self, dirty_train, dirty_test):
        clean_train, indicator_train = self.clean_df(dirty_train)
        clean_test, indicator_test = self.clean_df(dirty_test)
        return clean_train, indicator_train, clean_test, indicator_test

class DuplicatesCleaner(object):
    def __init__(self):
        super(DuplicatesCleaner, self).__init__()

    def fit(self, key_columns, df):
        self.keys = key_columns
    
    def detect(self, df, keys):
        key_col = pd.DataFrame(df, columns=keys)
        is_dup = key_col.duplicated(keep='first')
        is_dup = pd.DataFrame(is_dup, columns=['is_dup'])
        return is_dup

    def repair(self, df, is_dup):
        not_dup = (is_dup.values == False)
        df_clean = df[not_dup]
        return df_clean

    def clean_df(self, df):
        is_dup = self.detect(df, self.keys)
        df_clean = self.repair(df, is_dup)
        return df_clean, is_dup

    def clean(self, dirty_train, dirty_test):
        clean_train, indicator_train = self.clean_df(dirty_train)
        clean_test, indicator_test = self.clean_df(dirty_test)
        return clean_train, indicator_train, clean_test, indicator_test


def SD(x, nstd=3.0):
    # Standard Deviaiton Method (Univariate)
    mean, std = np.mean(x), np.std(x)
    cut_off = std * nstd
    lower, upper = mean - cut_off, mean + cut_off
    return lambda y: (y > upper) | (y < lower)

def IQR(x, k=1.5):
    # Interquartile Range (Univariate)
    q25, q75 = np.percentile(x, 25), np.percentile(x, 75)
    iqr = q75 - q25
    cut_off = iqr * k
    lower, upper = q25 - cut_off, q75 + cut_off
    return lambda y: (y > upper) | (y < lower)

def IF(x, contamination=0.01):
    # Isolation Forest (Univariate)
    IF = IsolationForest(contamination=contamination)
    IF.fit(x.reshape(-1, 1))
    return lambda y: (IF.predict(y.reshape(-1, 1)) == -1)

class OutlierCleaner(object):
    def __init__(self, detect_method, repairer=MVCleaner('delete'), **kwargs):
        super(OutlierCleaner, self).__init__()
        detect_fn_dict = {'SD':SD, 'IQR':IQR, "IF":IF}
        self.detect_method = detect_method
        self.detect_fn = detect_fn_dict[detect_method]
        self.repairer = repairer
        self.kwargs = kwargs
        self.tag = "{}_{}".format(detect_method, repairer.tag)
        self.is_fit = False
    
    def fit(self, df):
        num_df = df.select_dtypes(include='number')
        cat_df = df.select_dtypes(exclude='number')
        X = num_df.values
        m = X.shape[1]

        self.detectors = []
        for i in range(m):
            x = X[:, i]
            detector = self.detect_fn(x, **self.kwargs)
            self.detectors.append(detector)

        ind = self.detect(df)
        df_copy = df.copy()
        df_copy[ind] = np.nan
        self.repairer.fit(df_copy)
        self.is_fit = True

    def detect(self, df):
        num_df = df.select_dtypes(include='number')
        cat_df = df.select_dtypes(exclude='number')
        X = num_df.values
        m = X.shape[1]

        ind_num = np.zeros_like(num_df).astype('bool')
        ind_cat = np.zeros_like(cat_df).astype('bool')
        for i in range(m):
            x = X[:, i]
            detector = self.detectors[i]
            is_outlier = detector(x)
            ind_num[:, i] = is_outlier

        ind_num = pd.DataFrame(ind_num, columns=num_df.columns)
        ind_cat = pd.DataFrame(ind_cat, columns=cat_df.columns)
        ind = pd.concat([ind_num, ind_cat], axis=1).reindex(columns=df.columns)
        return ind

    def repair(self, df, ind):
        df_copy = df.copy()
        df_copy[ind] = np.nan
        df_clean, _ = self.repairer.clean_df(df_copy)
        return df_clean

    def clean_df(self, df, ignore=None):
        if not self.is_fit:
            print("Must fit before clean")
            sys.exit()
        ind = self.detect(df)
        if ignore is not None:
            ind.loc[:, ignore] = False
        df_clean = self.repair(df, ind)
        return df_clean, ind

    def clean(self, dirty_train, dirty_test):
        clean_train, indicator_train = self.clean_df(dirty_train)
        clean_test, indicator_test = self.clean_df(dirty_test)
        return clean_train, indicator_train, clean_test, indicator_test