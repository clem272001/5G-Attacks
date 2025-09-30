import os
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score
from sklearn.metrics import classification_report, confusion_matrix, roc_curve, roc_auc_score, precision_recall_curve, average_precision_score, auc

from sklearn.tree import export_graphviz
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
       # df_train = df_train.drop(columns=['frame.number','source_file'])
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

        #Création du modèle 
        self.model = RandomForestClassifier(class_weight='balanced', max_depth= 10, max_features= 'sqrt', min_samples_split=2, n_estimators=100, random_state= 42)  # Parallélisation
        self.model.fit(self.X_train, self.Y_train)

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
    # Transformer les labels en binaire
    bal_acc = balanced_accuracy_score(y_true, y_pred)
    print("Balanced accuracy: ",bal_acc)
    y_true_bin = np.array([-1 if y == -1 else 1 for y in y_true])
    y_pred_bin = np.array([-1 if y == -1 else 1 for y in y_pred])
    
    
    # Calculer la confusion matrix binaire
    cm2 = confusion_matrix(y_true_bin, y_pred_bin, labels=[1, -1])
    tp, fn, fp, tn = cm2[0, 0], cm2[0, 1], cm2[1, 0], cm2[1, 1]
    print(f"TP: {tp} | FN: {fn} | FP: {fp} | TN: {tn}")
    print("Binary Confusion Matrix:")
    print(cm2)
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
    
    print("\nValeurs uniques dans Y_test :", np.unique(detection.Y_test))
    print(pd.Series(detection.Y_test).value_counts())

    print("\nValeurs uniques dans Y_predit :", np.unique(Y_predit))
    print(pd.Series(Y_predit).value_counts())

    #Evaluation du modèle
    evaluate_predictions(detection.Y_test, Y_predit)

#----------------- Création de la courbe ROC -----------------# 
from sklearn.preprocessing import label_binarize

# Probabilités de toutes les classes
y_score = detection.model.predict_proba(detection.X_test)
y_true = detection.Y_test

# Vérifier le nombre de classes
classes = np.unique(y_true)

if len(classes) == 2:
    # ----- Cas binaire -----
    y_proba = y_score[:, 1]  # proba pour la classe positive
    fpr, tpr, thresholds = roc_curve(y_true, y_proba, pos_label=classes[1])
    roc_auc = auc(fpr, tpr)

    plt.figure()
    plt.plot(fpr, tpr, color='blue', lw=2,
             label=f"Random Forest (AUC = {roc_auc:.2f})")
    plt.plot([0, 1], [0, 1], color='gray', linestyle='--')
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("Courbe ROC - Random Forest (Binaire)")
    plt.legend(loc="lower right")
    plt.show()

else:
    # ----- Cas multi-classes -----
    y_test_bin = label_binarize(y_true, classes=classes)
    n_classes = y_test_bin.shape[1]

    fpr, tpr, roc_auc = {}, {}, {}

    for i in range(n_classes):
        fpr[i], tpr[i], _ = roc_curve(y_test_bin[:, i], y_score[:, i])
        roc_auc[i] = auc(fpr[i], tpr[i])

    plt.figure()
    for i in range(n_classes):
        plt.plot(fpr[i], tpr[i], lw=2,
                 label=f"Classe {classes[i]} (AUC = {roc_auc[i]:.2f})")

    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("Courbes ROC - Random Forest (One-vs-Rest)")
    plt.legend(loc="lower right")
    plt.show()



