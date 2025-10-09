import os
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    classification_report, confusion_matrix, precision_recall_curve, average_precision_score, f1_score, precision_score, recall_score
)
from sklearn.metrics import balanced_accuracy_score

class DetectionIsolationForest:
    def __init__(self, df_train_csv, df_test_csv):

        # Conversion des types pour réduire la mémoire
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

        # Chargement train
        df_train = pd.read_csv(df_train_csv, sep=';', dtype=dtypes)
        #df_train = df_train.drop(columns=['frame.number'])
        print("Df train len : ", len(df_train))
        sorted_columns = sorted(df_train.columns)
        self.X_train = df_train[sorted_columns].copy()
        del df_train

        if 'ip.opt.time_stamp' in self.X_train.columns:
            self.X_train = self.X_train.drop('ip.opt.time_stamp', axis=1)

        # Chargement test
        df_test = pd.read_csv(df_test_csv, sep=';', dtype=dtypes)
        #df_test = df_test.drop(columns=['frame.number', 'source_file'])
        print("Df test len : ", len(df_test))
        sorted_columns = sorted(df_test.columns)
        self.df_test = df_test[sorted_columns].copy()

        self.X_test = self.df_test.drop('ip.opt.time_stamp', axis=1)

        # Labels anomalies : -1 = anomalie, 1 = normal
        self.df_test['anomaly'] = df_test.apply(self.tag_anomalies, axis=1)
        self.Y_test = self.df_test['anomaly']

        # Modèle Isolation Forest
        self.model = IsolationForest(
            bootstrap= False, 
            max_features=0.5, max_samples=1500, n_estimators=50, n_jobs=-1, random_state= 42, verbose= 0, warm_start=False
        )
        print(len(self.X_train.columns))
        print(len(self.X_test.columns))
        print(self.X_train.columns)
        print(self.X_test.columns)
        self.model.fit(self.X_train)

    #----------------- Fonctions labels -----------------#

    def tag_anomalies(self, row):
        if row['ip.opt.time_stamp'] in range(0, 7):
            return -1  # Anomaly
        else:
            return 1  # Normal

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
            else: return 0  # Missclassified
        else:
            if row['ip.opt.time_stamp'] == 0: return 2  # DoS
            elif row['ip.opt.time_stamp'] == 1: return 3  # deletion
            elif row['ip.opt.time_stamp'] == 2: return 4  # modification
            elif row['ip.opt.time_stamp'] == 3: return 5  # Nmap
            elif row['ip.opt.time_stamp'] == 4: return 6  # Reverse shell
            elif row['ip.opt.time_stamp'] == 5: return 7  # pdn type
            elif row['ip.opt.time_stamp'] == 6: return 8  # pdn type
            else: return 1  # Normal


#----------------- Métriques -----------------#

def evaluate_predictions(y_true, y_pred):
    cm = confusion_matrix(y_true, y_pred, labels=[-1, 1])
    tp, fn, fp, tn = cm[0, 0], cm[0, 1], cm[1, 0], cm[1, 1]
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    print(f"Confusion Matrix:\n{cm}")
    print(f"TP: {tp} | FN: {fn} | FP: {fp} | TN: {tn}")
    print(f"Precision: {precision:.6f}")
    print(f"Recall   : {recall:.6f}")
    print(f"F1 Score : {f1:.6f}")
    print(classification_report(y_true, y_pred, digits=4, labels=[-1, 1], zero_division=0))
    bal_acc = balanced_accuracy_score(y_true, y_pred)
    print("Balanced accuracy: ",bal_acc)
    return cm, precision, recall, f1


#----------------- Main -----------------#

if __name__ == "__main__":

    df_train_csv = 'dataset_1_final.csv'
    df_test_csv = 'dataset_3_final.csv'

    detection = DetectionIsolationForest(df_train_csv, df_test_csv)

    # Prédictions initiales
    Y_pred = detection.model.predict(detection.X_test)
    detection.df_test['predictions'] = Y_pred

    detection.df_test['anomaly'] = detection.df_test.apply(
        detection.classify_anomalies, axis=1, prediction=False
    )
    Y_test_classified = detection.df_test['anomaly']

    print("\nValeurs uniques dans Y_test :", np.unique(detection.Y_test))
    print(pd.Series(detection.Y_test).value_counts())

    print("\nValeurs uniques dans Y_pred :", np.unique(Y_pred))
    print(pd.Series(Y_pred).value_counts())

    evaluate_predictions(detection.Y_test, Y_pred)

    # Courbe PR (avec y_true binaire pour scikit-learn)
    scores = detection.model.decision_function(detection.X_test)
    y_true_bin = np.where(detection.Y_test == -1, 1, 0)  # 1 = anomalie, 0 = normal
    precision, recall, thresholds = precision_recall_curve(y_true_bin, -scores)

    ap = average_precision_score(y_true_bin, -scores)

    f1_scores = 2 * (precision[:-1] * recall[:-1]) / (precision[:-1] + recall[:-1])
    f1_scores = np.nan_to_num(f1_scores)

    best_index = np.argmax(f1_scores)
    best_threshold = thresholds[best_index]

    precision_raw, recall_raw, thresholds = precision_recall_curve(y_true_bin, -scores)
    ap = average_precision_score(y_true_bin, -scores)

    macro_precision_list = []
    macro_recall_list = []
    macro_f1_list = []

    for t in thresholds:
        y_pred = (-scores >= t).astype(int)
        macro_precision = precision_score(y_true_bin, y_pred, average='macro', zero_division=0)
        macro_recall = recall_score(y_true_bin, y_pred, average='macro', zero_division=0)
        macro_f1 = f1_score(y_true_bin, y_pred, average='macro', zero_division=0)
        macro_precision_list.append(macro_precision)
        macro_recall_list.append(macro_recall)
        macro_f1_list.append(macro_f1)

    best_index = np.argmax(macro_f1_list)
    best_threshold = thresholds[best_index]

    # --- Plot macro-averaged Precision/Recall ---
    plt.figure(figsize=(10, 6))
    plt.plot(thresholds, macro_precision_list, label='Macro Precision', linestyle='--', color='blue', linewidth=4)
    plt.plot(thresholds, macro_recall_list, label='Macro Recall', color='orange', linewidth=4)
    plt.axvline(x=best_threshold, color='red', linestyle='--', linewidth=3,
                label=f'Optimal threshold = {best_threshold:.4f}')
    plt.xlabel("Threshold", fontsize=40)
    plt.ylabel("Macro-averaged Score", fontsize=40)
    plt.xticks(fontsize=35)
    plt.yticks(fontsize=35)
    plt.legend(fontsize=28, loc='upper right')
    plt.grid(True)
    plt.show()

    print(f"Optimal threshold (macro F1 max): {best_threshold:.4f}")
    print(f"Macro Precision: {macro_precision_list[best_index]:.6f}, "
          f"Macro Recall: {macro_recall_list[best_index]:.6f}, "
          f"Macro F1: {macro_f1_list[best_index]:.6f}")
    print(f"Average Precision (AUC-PR): {ap:.6f}")

    print(f"Meilleur seuil (F1 max) : {best_threshold:.4f}")
    print(f"Precision: {precision[best_index]:.6f}, Recall: {recall[best_index]:.6f}, F1: {f1_scores[best_index]:.6f}")

    #----------------- Nouvelles prédictions basées sur le seuil -----------------#

    y_pred_bin = np.where(-scores >= best_threshold, 1, 0)  # 1 = anomalie
    y_true_bin = np.where(detection.Y_test == -1, 1, 0)

    f1_check = f1_score(y_true_bin, y_pred_bin)
    print(f"\nF1 recalculé après application du seuil (doit matcher courbe PR): {f1_check:.6f}")

    # Reconversion en [-1, 1] pour cohérence avec IsolationForest
    y_pred = np.where(y_pred_bin == 1, -1, 1)
    cm_seuil, precision_s, recall_s, f1_s = evaluate_predictions(detection.Y_test, y_pred)

     # Classification multi-classes
    detection.df_test['predictions'] = y_pred
    detection.df_test['predictions'] = detection.df_test.apply(
        detection.classify_anomalies, axis=1, prediction=True
    )

    Y_test_classified = detection.df_test.apply(
        detection.classify_anomalies, axis=1, prediction=False
    )
    Y_pred_classified = detection.df_test['predictions']

    best_cm = confusion_matrix(Y_test_classified, Y_pred_classified)
    print("\nMatrice multi-classes :\n", best_cm)

    #----------------- Évaluation multi-classes -----------------#

    class_names = [
        'Miss', 'Normal', 'PFCP DoS', 'PFCP Session Deletion',
        'PFCP Session Modifications', 'Nmap', 'Reverse shell',
        'Pdn type', 'cve 2025 29646'
    ]

    precision_total = recall_total = f1_score_total = 0
    for i, class_name in enumerate(class_names):
        if class_name != "Miss":
            tp = best_cm[i, i]
            fp = best_cm[:, i].sum() - tp
            fn = best_cm[i, :].sum() - tp
            tn = best_cm.sum() - (tp + fp + fn)

            print(f"\nClasse '{class_name}':")
            print(f"TP={tp}, FP={fp}, FN={fn}, TN={tn}")

            prec = tp / (tp + fp) if (tp + fp) > 0 else 0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0

            precision_total += prec
            recall_total += rec
            f1_score_total += f1

            print(f"Precision: {prec*100:.2f}% | Recall: {rec*100:.2f}% | F1: {f1*100:.2f}%")

    n_classes = len(class_names) - 1
    print(f"\nMoyenne Precision: {(precision_total/n_classes)*100:.2f}%")
    print(f"Moyenne Recall   : {(recall_total/n_classes)*100:.2f}%")
    print(f"Moyenne F1-Score : {(f1_score_total/n_classes)*100:.2f}%")
