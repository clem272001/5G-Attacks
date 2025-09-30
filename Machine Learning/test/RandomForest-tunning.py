import os
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix, roc_curve, roc_auc_score, precision_recall_curve, average_precision_score, make_scorer, f1_score

from sklearn.tree import export_graphviz
from multiprocessing import cpu_count
import time

# import graphviz

class DetectionRandomForest:
    def __init__(self, df_train_csv, df_test_csv):#, parameters):

#----------------- Conversion des types de données pour réduire l'utilisation de la mémoire ----------------- #
        
        dtypes = {}
        sample = pd.read_csv(df_train_csv, sep=';', nrows=5)
        for col in sample.columns:
            if sample[col].dtype == 'float64':
                dtypes[col] = 'float32'
            elif sample[col].dtype == 'int64':
                dtypes[col] = 'int8'
            else:
                dtypes[col] = sample[col].dtype
        del sample

#----------------- Chargement des dataset avec les types changés pour l'optimisation de la mémoire ----------------- #
        df_train = pd.read_csv(df_train_csv, sep=';', dtype=dtypes)
        #df_train = df_train.drop(columns=['frame.number','source_file'])
        df_train['ip.opt.time_stamp'] = df_train['ip.opt.time_stamp'].fillna(-1)
        print("Df train len : ",len(df_train))
        sorted_columns = sorted(df_train.columns)
         # Enlever la colonne cible dans X_test
        self.df_train = df_train[sorted_columns].copy()
        self.X_train = self.df_train.drop('ip.opt.time_stamp', axis=1)
       
        self.Y_train = self.df_train['ip.opt.time_stamp']
        
        del df_train, self.df_train

        # Chargement optimisé du test  
        df_test = pd.read_csv(df_test_csv, sep=';', dtype=dtypes)
        #df_test = df_test.drop(columns=['frame.number','source_file'])
        df_test['ip.opt.time_stamp'] = df_test['ip.opt.time_stamp'].fillna(-1)

        print("Df test len : ",len(df_test))
        sorted_columns = sorted(df_test.columns)
        self.df_test = df_test[sorted_columns].copy()

        # Enlever la colonne cible dans X_test
        self.X_test = self.df_test.drop('ip.opt.time_stamp', axis=1)
        # Conversion en float 32
        # self.X_test = self.X_test.astype('float32')

        #Création de la colonne anomaly en fonction des labels présents dans ip.opt.time_stamp
        self.Y_test = self.df_test['ip.opt.time_stamp']

        # param_grid = {'bootstrap': [True], 'ccp_alpha': [1.0], 'class_weight': ['balanced_subsample'], 
        #                            'criterion': ['gini'], 'max_depth': [15], 'max_features': ['sqrt'], 
        #                            'max_leaf_nodes': [20], 'max_samples': [0.7], 'min_impurity_decrease': [0.01],
        #                            'min_weight_fraction_leaf': [0.01], 'n_estimators': [200], 'oob_score': [False], 
        #                            'random_state': [42], 'verbose': [0], 'warm_start': [False]}
        param_grid = {
            'n_estimators': [100, 200, 300],
            'max_depth': [10, 15, 20],
            'max_features': ['sqrt', 'log2'],
            'min_samples_split': [2, 5, 10],
            'class_weight': ['balanced', 'balanced_subsample', None], 'random_state': [42]
}

        
        # Define the model
        rf = RandomForestClassifier()
        total_cores = cpu_count()
        print(total_cores)
        n_jobs = total_cores - 14 if total_cores > 2 else 1
        print(n_jobs)
        start_time = time.time()
        grid_search = GridSearchCV(estimator=rf, param_grid=param_grid, 
                                cv=3, n_jobs=n_jobs, verbose=3, scoring=make_scorer(f1_score, average='macro', zero_division=0))
        # Fit the grid search to the data
        grid_search.fit(self.X_train, self.Y_train)
        best_rf = grid_search.best_estimator_
        best_params = grid_search.best_params_
        self.best_params = best_params
        self.model = best_rf
        gridsearch_time = time.time() - start_time 
        print((time.time() - start_time) / 60, 'minutes for gridsearch') 
 

#----------------- Fonctions label et classification des anomalies -----------------# 

    

#----------------- Metriques et performances -----------------# 

#Fonction pour évaluer une prédiction en affichant matrice de confusion et métriques
def evaluate_predictions(y_true, y_pred):
    labels = sorted(np.unique(list(y_true) + list(y_pred)))
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    print("Confusion Matrix (multi-classes):")
    print("Labels:", labels)
    print(cm)

    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, labels=labels, digits=4, zero_division=0))
    
    return cm

""" Avec les labels [-1,1] ça change la matrice et l'ordre des valeurs
           Prédit
          -1     1
        -------------
Réel -1 | TP   | FN  |
Réel  1 | FP   | TN  |

"""

#----------------- Main -----------------# 

if __name__ == "__main__":

#----------------- Création du modèle et prédiction -----------------# 
    # training dataset
    df_train_csv = 'dataset_2_scaled.csv'
    # test dataset
    df_test_csv = 'dataset_3_scaled.csv'

    detection = DetectionRandomForest(df_train_csv, df_test_csv)#, parameters)
    #predit on the test data
    Y_predit = detection.model.predict(detection.X_test)
    print(detection.best_params)
    print("\nValeurs uniques dans Y_test :", np.unique(detection.Y_test))
    print(pd.Series(detection.Y_test).value_counts())

    print("\nValeurs uniques dans Y_predit :", np.unique(Y_predit))
    print(pd.Series(Y_predit).value_counts())
  
    #Evaluation du modèle
    evaluate_predictions(detection.Y_test, Y_predit)

#----------------- Création de la courbe Précision/Rappel et recherche du seuil optimal selon f1-score max -----------------# 

    
