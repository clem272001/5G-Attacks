# iso2_tunning.py
import os
import sys
import time
import numpy as np
import pandas as pd
from multiprocessing import cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed

import matplotlib.pyplot as plt
from tqdm import tqdm

from sklearn.ensemble import IsolationForest
from sklearn.model_selection import ParameterGrid
from sklearn.metrics import (
    confusion_matrix,
    precision_recall_curve,
    average_precision_score,
    f1_score,
)

# ----------------- Classe principale ----------------- #

class DetectionIsolationForest:
    def __init__(self, df_train_csv, df_test_csv):
        # --- Conversion des types mémoire ---
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

        # --- Chargement train ---
        df_train = pd.read_csv(df_train_csv, sep=';', dtype=dtypes)
        print("Df train len : ", len(df_train))
        sorted_columns = sorted(df_train.columns)
        self.X_train = df_train[sorted_columns].copy()
        del df_train

        if 'ip.opt.time_stamp' in self.X_train.columns:
            self.X_train = self.X_train.drop('ip.opt.time_stamp', axis=1)

        # --- Chargement test ---
        df_test = pd.read_csv(df_test_csv, sep=';', dtype=dtypes)
        print("Df test len : ", len(df_test))
        sorted_columns = sorted(df_test.columns)
        self.df_test = df_test[sorted_columns].copy()
        self.X_test = self.df_test.drop('ip.opt.time_stamp', axis=1)

        # Labels binaires (-1 anomalie, 1 normal)
        self.df_test['anomaly'] = df_test.apply(self.tag_anomalies, axis=1)
        self.Y_test = self.df_test['anomaly']

        # Placeholder
        self.model = None
        self.best_threshold_ = None

    # ----------------- Fonctions labels ----------------- #

    def tag_anomalies(self, row):
        if row['ip.opt.time_stamp'] in range(0, 7):
            return -1
        else:
            return 1

    def classify_anomalies(self, row, prediction):
        if prediction:
            if row['anomaly'] == 2 and row['predictions'] == -1: return 2
            elif row['anomaly'] == 3 and row['predictions'] == -1: return 3
            elif row['anomaly'] == 4 and row['predictions'] == -1: return 4
            elif row['anomaly'] == 5 and row['predictions'] == -1: return 5
            elif row['anomaly'] == 6 and row['predictions'] == -1: return 6
            elif row['anomaly'] == 7 and row['predictions'] == -1: return 7
            elif row['anomaly'] == 8 and row['predictions'] == -1: return 8
            elif row['anomaly'] == 9 and row['predictions'] == -1: return 9
            elif row['anomaly'] == 1 and row['predictions'] == 1: return 1
            else: return 0
        else:
            if row['ip.opt.time_stamp'] == 0: return 2
            elif row['ip.opt.time_stamp'] == 1: return 3
            elif row['ip.opt.time_stamp'] == 2: return 4
            elif row['ip.opt.time_stamp'] == 3: return 5
            elif row['ip.opt.time_stamp'] == 4: return 6
            elif row['ip.opt.time_stamp'] == 5: return 7
            elif row['ip.opt.time_stamp'] == 6: return 8
            else: return 1

    # ----------------- Tâche d'entraînement + seuil optimal ----------------- #

    def run_isolation_forest(self, param_combination, best=False):
        model = IsolationForest(**param_combination)
        model.fit(self.X_train)

        # Scores
        scores = model.decision_function(self.X_test)

        # Labels binaires forcés
        y_true = np.where(self.Y_test == -1, -1, 1)
        y_true_bin = np.where(y_true == -1, 1, 0)

        precision, recall, thresholds = precision_recall_curve(y_true_bin, -scores)
        denom = precision[:-1] + recall[:-1]
        f1_scores = np.divide(2 * (precision[:-1] * recall[:-1]), denom, out=np.zeros_like(denom), where=denom != 0)
        f1_scores = np.nan_to_num(f1_scores)
        best_index = np.argmax(f1_scores)
        best_threshold = thresholds[best_index]

        # Prédiction avec meilleur seuil
        y_pred_bin = np.where(-scores > best_threshold, 1, 0)
        y_pred = np.where(y_pred_bin == 1, -1, 1)

        cm, p, r, f1 = evaluate_predictions(y_true, y_pred)

        if best:
            self.model = model
            self.best_threshold_ = best_threshold

            ap = average_precision_score(y_true_bin, -scores)
            plt.figure(figsize=(10, 6))
            plt.plot(thresholds, precision[:-1], label='Precision', color='blue')
            plt.plot(thresholds, recall[:-1], label='Recall', color='orange')
            plt.axvline(x=best_threshold, color='red', linestyle='--',
                        label=f'Optimal threshold = {best_threshold:.4f}')
            plt.xlabel("Threshold")
            plt.ylabel("Score")
            plt.title(f"Precision/Recall vs Threshold (AP={ap:.4f})")
            plt.legend()
            plt.grid(True)
            plt.show()

            print(f"Meilleur seuil (F1 max) : {best_threshold:.4f}")
            print(f"Precision: {precision[best_index]:.6f}, Recall: {recall[best_index]:.6f}, F1: {f1_scores[best_index]:.6f}")

            f1_check = f1_score(y_true_bin, y_pred_bin)
            print(f"\nF1 recalculé après seuil: {f1_check:.6f}")

            self.df_test['predictions'] = y_pred
            self.df_test['predictions'] = self.df_test.apply(self.classify_anomalies, axis=1, prediction=True)

        return cm, f1, p, r, model.get_params()

# ----------------- Métriques ----------------- #

def evaluate_predictions(y_true, y_pred):
    cm = confusion_matrix(y_true, y_pred, labels=[-1, 1])
    tp, fn, fp, tn = cm[0, 0], cm[0, 1], cm[1, 0], cm[1, 1]
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    print(f"Confusion Matrix:\n{cm}")
    print(f"TP: {tp} | FN: {fn} | FP: {fp} | TN: {tn}")
    print(f"Precision: {precision:.6f}")
    print(f"Recall   : {recall:.6f}")
    print(f"F1 Score : {f1:.6f}")
    return cm, precision, recall, f1

# ----------------- Main ----------------- #

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python iso2_tunning.py <number_of_iterations>")
        sys.exit(1)
    iterations = int(sys.argv[1])
    print(f'number_of_iterations = {iterations}\n')

    df_train_csv = 'dataset_1_scaled.csv'
    df_test_csv  = 'dataset_3_scaled.csv'

    detection = DetectionIsolationForest(df_train_csv, df_test_csv)

    param_grid = {
        'bootstrap':    [True, False],
        'max_features': [1.0, 0.8, 0.5, 0.9, 0.6, 0.7, 0.4],
        'max_samples':  [100, 256, 500, 1000, 1100, 1200, 1300, 1400, 1500, 1600],
        'n_estimators': [50, 100, 150, 200],
        'verbose':      [0],
    }
    param_grid['random_state'] = [42]#[np.random.randint(0, 2**31 - 1) for _ in range(iterations)]
    param_combinations = list(ParameterGrid(param_grid))

    dict_models = {k: [] for k in range(len(param_combinations))}

    total_cores = cpu_count()
    n_jobs = max(1, total_cores - 4)
    print(f"Usage : {n_jobs}/{total_cores} cores\n")

    start_time = time.time()
    with tqdm(total=len(param_combinations), desc=f"Calcul des combinaisons de paramètres {len(param_combinations)}") as pbar:
        with ProcessPoolExecutor(max_workers=1) as executor:
            futures = [
                executor.submit(detection.run_isolation_forest, param_combinations[c], False)
                for c in range(len(param_combinations))
            ]
            for idx, future in enumerate(as_completed(futures)):
                try:
                    cm, f1, p, r, params = future.result()
                    dict_models[idx] = [f1, p, r, params]
                except Exception as e:
                    print(f"Erreur combo {idx}: {e}")
                    dict_models[idx] = [0.0, 0.0, 0.0, {'error': str(e)}]
                pbar.update(1)

    elapsed = time.time() - start_time
    print(f"\nTuning terminé en {elapsed/60:.2f} min")

    max_f1 = -1
    best_params = None
    for combo_idx, result in dict_models.items():
        if not result:
            continue
        f1, p, r, params = result
        if isinstance(params, dict) and 'error' in params:
            continue
        if f1 > max_f1:
            max_f1 = f1
            best_params = params

    if best_params is None:
        print("Aucun modèle valide trouvé, arrêt.")
        sys.exit(2)

    print(f"\nMeilleur F1 (tuning): {max_f1:.4f}")
    print(f"Paramètres sélectionnés: {best_params}")

    cm_seuil, f1_final, precision_final, recall_final, _ = detection.run_isolation_forest(best_params, best=True)

    
