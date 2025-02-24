import numpy as np
import pandas as pd
from clean_method import MVCleaner, DuplicatesCleaner, OutlierCleaner

def mv_repair(df, method):
    if method == 'delete':
        mv_obj = MVCleaner(method = 'delete')
        mv_obj.fit(df)
        return mv_obj.clean_df(df)[0]
    else:
        num, cat = method.split('-')
        mv_obj = MVCleaner(method = 'impute', num = num, cat=cat)
        mv_obj.fit(df)
        return mv_obj.clean_df(df)[0]
 
def outlier_repair(df, detect_method, repair_method):
    outlier_obj = OutlierCleaner(detect_method = detect_method, 
                                 repairer=MVCleaner(method = 'impute',
                                        num = repair_method, cat='mode'))
    outlier_obj.fit(df)
    return outlier_obj.clean_df(df)[0]
    
def duplicate_repair(df, key_columns):
    dup_obj = DuplicatesCleaner()
    dup_obj.fit(key_columns, df)
    return dup_obj.clean_df(df)[0]


class ErrorCleaner(object):
    def __init__(self, df, cleaning_setup):
        self.df = df
        self.cleaning_setup = cleaning_setup.to_dict()
        self.data_issues = self.cleaning_setup.keys()
        
        self.df_copy = self.df.copy()
        
    def clean_all(self, key_columns = None):
        if 'mv_repair' in self.data_issues:
            self.df_copy = mv_repair(self.df_copy, self.cleaning_setup['mv_repair'])
            
        if 'outlier_detection' in self.data_issues:
            if self.cleaning_setup['outlier_detection'] != 'none':
                self.df_copy = outlier_repair(self.df_copy, 
                                              self.cleaning_setup['outlier_detection'],
                                              self.cleaning_setup['outlier_repair'])
                
        if 'duplicate_repair' in self.data_issues:
            if self.cleaning_setup['duplicate_repair'] != 'NA':
                self.df_copy = duplicate_repair(self.df_copy, key_columns)
                
        return self.df_copy
    