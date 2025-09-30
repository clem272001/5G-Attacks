import os
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import GridSearchCV
from imblearn.over_sampling import SMOTE
from sklearn.metrics import (
    classification_report, confusion_matrix
)


class DetectionKNN:
    def __init__(self, df_train_csv, df_test_csv):
        # ----------------- Conversion des types ----------------- #
        dtypes = {}
        sample = pd.read_csv(df_train_csv, sep=';', nrows=5)
        for col in sample.columns:
            if sample[col].dtype == 'float64':
                dtypes[col] = 'float32'
            elif sample[col].dtype == 'int64':
                dtypes[col] = 'int32'
            else:
                dtypes[col] = sample[col].dtype
        del sample

        # ----------------- Train ----------------- #
        df_train = pd.read_csv(df_train_csv, sep=';', dtype=dtypes)
        df_train = df_train.drop(columns=['frame.number', 'source_file'], errors="ignore")
        df_train['ip.opt.time_stamp'] = df_train['ip.opt.time_stamp'].fillna(-1)
        print("Df train len:", len(df_train))

        sorted_columns = sorted(df_train.columns)
        df_train = df_train[sorted_columns].copy()
        self.X_train = df_train.drop('ip.opt.time_stamp', axis=1)
        self.Y_train = df_train['ip.opt.time_stamp']

        # ----------------- Test ----------------- #
        df_test = pd.read_csv(df_test_csv, sep=';', dtype=dtypes)
        df_test = df_test.drop(columns=['frame.number', 'source_file'], errors="ignore")
        df_test['ip.opt.time_stamp'] = df_test['ip.opt.time_stamp'].fillna(-1)
        print("Df test len:", len(df_test))

        sorted_columns = sorted(df_test.columns)
        df_test = df_test[sorted_columns].copy()
        self.X_test = df_test.drop('ip.opt.time_stamp', axis=1)
        self.Y_test = df_test['ip.opt.time_stamp']

        # ----------------- GridSearchCV ----------------- #
        # param_grid = {
        #     'n_neighbors': [3, 5, 7, 9],
        #     'weights': ['uniform', 'distance'],
        #     'p': [1, 2],  # 1=Manhattan, 2=Euclidean
        #     'metric': ['minkowski']
        # }
        param_grid = {
            'n_neighbors': [3, 15, 20, 30, 50],
            'weights': ['uniform', 'distance'],
            'metric': ['euclidean', 'manhattan', 'chebyshev','minkowski'],
            'algorithm': ['auto','ball_tree', 'kd_tree', 'brute'], 'p':[1,2]
          # seulement utilisé si metric='minkowski'
        }
        grid = GridSearchCV(
            estimator=KNeighborsClassifier(),
            param_grid=param_grid,
            cv=3,  # validation croisée
            scoring='balanced_accuracy',
            n_jobs=-1,
            verbose=2
        )
        sm = SMOTE(random_state=42)
        X_res, y_res = sm.fit_resample(self.X_train, self.Y_train)

        grid.fit(X_res, y_res)
        print("\nMeilleurs paramètres KNN :", grid.best_params_)
        print("Meilleur score (f1_macro) :", grid.best_score_)

        # modèle final optimisé
        self.model = grid.best_estimator_

    def predict(self):
        return self.model.predict(self.X_test)


# ----------------- Évaluation ----------------- #
def evaluate_predictions(y_true, y_pred):
    labels = sorted(np.unique(list(y_true) + list(y_pred)))
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    print("\nConfusion Matrix (multi-classes):")
    print("Labels:", labels)
    print(cm)

    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, labels=labels, digits=4, zero_division=0))
    
    return cm


# ----------------- Main ----------------- #
if __name__ == "__main__":
    df_train_csv = 'dataset_2_scaled.csv'
    df_test_csv = 'dataset_2_scaled.csv'

    detection = DetectionKNN(df_train_csv, df_test_csv)

    Y_pred = detection.predict()

    print("\nValeurs uniques dans Y_test :", np.unique(detection.Y_test))
    print(pd.Series(detection.Y_test).value_counts())

    print("\nValeurs uniques dans Y_pred :", np.unique(Y_pred))
    print(pd.Series(Y_pred).value_counts())

    evaluate_predictions(detection.Y_test, Y_pred)

