import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Fichiers d'entrée et sortie
input_jeu1 = "dataset_1_encoded.csv"
input_jeu2 = "dataset_2_encoded.csv"
input_jeu3 = "dataset_3_encoded.csv"

output_jeu1 = "dataset_1_filtered.csv"
output_jeu2 = "dataset_2_filtered.csv"
output_jeu3 = "dataset_3_filtered.csv"

chunksize = 50_000


def compute_pairwise_correlations(file_path, ref_col="ip.opt.time_stamp",
                                  special_cols=None):
    """
    Calcule la matrice de corrélation d'un dataset,
    retourne matrice et corrélation avec le label.
    """
    if special_cols is None:
        special_cols = ["ip.opt.time_stamp", "frame.number"]

    print(f"Chargement échantillon {file_path}...")
    df = pd.read_csv(file_path, sep=';', nrows=5000, low_memory=False)

    # Forcer la colonne ref_col en numérique
    if ref_col in df.columns:
        df[ref_col] = pd.to_numeric(df[ref_col], errors="coerce").fillna(-1).astype(int)

    # Colonnes numériques sauf spéciales
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c not in special_cols +
                    ['tcp.srcport', 'tcp.dstport', 'udp.srcport', 'udp.dstport']]

    # Matrice de corrélation
    corr_matrix = df[numeric_cols].corr(method="pearson")

    # Corrélation avec le label
    special_corr = df[numeric_cols + [ref_col]].corr(method="pearson")[ref_col].drop(ref_col)

    return numeric_cols, corr_matrix, special_corr


def find_common_correlated_pairs(corr2, corr3, cols, special_corr2, special_corr3, threshold=0.90):
    """
    Trouve les paires très corrélées dans corr2 ET corr3,
    choisit la colonne à supprimer selon la corrélation avec le label.
    """
    correlated_pairs = []
    cols_to_remove = set()

    for i, col1 in enumerate(cols):
        for j in range(i + 1, len(cols)):
            col2 = cols[j]

            # Vérifier si la paire est très corrélée dans les deux matrices
            c2 = corr2.loc[col1, col2] if col1 in corr2 and col2 in corr2 else None
            c3 = corr3.loc[col1, col2] if col1 in corr3 and col2 in corr3 else None

            if c2 is not None and c3 is not None and abs(c2) >= threshold and abs(c3) >= threshold:
                correlated_pairs.append((col1, col2, c2, c3))

                # Choisir colonne à supprimer selon corrélation au label
                corr1 = abs(special_corr2.get(col1, 0)) + abs(special_corr3.get(col1, 0))
                corr2_val = abs(special_corr2.get(col2, 0)) + abs(special_corr3.get(col2, 0))

                if corr1 < corr2_val:
                    cols_to_remove.add(col1)
                    print(f"Suppression {col1} (corr label {corr1:.3f}) vs {col2} (corr label {corr2_val:.3f})")
                else:
                    cols_to_remove.add(col2)
                    print(f"Suppression {col2} (corr label {corr2_val:.3f}) vs {col1} (corr label {corr1:.3f})")

    print(f"{len(correlated_pairs)} paires corrélées détectées dans les DEUX jeux (|corr| >= {threshold})")
    return cols_to_remove


def apply_filter_and_save(input_file, output_file, cols_to_drop):
    """Filtre les colonnes à supprimer et sauvegarde en chunké."""
    write_header = True
    for chunk in pd.read_csv(input_file, sep=';', chunksize=chunksize, low_memory=False):
        chunk_filtered = chunk.drop(columns=cols_to_drop, errors='ignore')
        chunk_filtered.to_csv(output_file, sep=';', index=False,
                              header=write_header, mode='w' if write_header else 'a')
        write_header = False


def compute_pearson_filter_multi():
    # Corrélation séparée sur jeu_2 et jeu_3
    cols2, corr2, special_corr2 = compute_pairwise_correlations(input_jeu2)
    cols3, corr3, special_corr3 = compute_pairwise_correlations(input_jeu3)

    # Colonnes communes (sinon pas comparable)
    common_cols = sorted(set(cols2).intersection(set(cols3)))
    print(f"Colonnes numériques communes aux deux attaques : {len(common_cols)}")

    # Trouver colonnes à supprimer
    cols_to_remove = find_common_correlated_pairs(corr2, corr3, common_cols,
                                                  special_corr2, special_corr3,
                                                  threshold=0.90)

    print("Colonnes finales à retirer globalement :")
    for col in sorted(cols_to_remove):
        print(f" - {col}")

    # Appliquer suppression sur les 3 jeux
    apply_filter_and_save(input_jeu1, output_jeu1, cols_to_remove)
    apply_filter_and_save(input_jeu2, output_jeu2, cols_to_remove)
    apply_filter_and_save(input_jeu3, output_jeu3, cols_to_remove)

    print("Étape Pearson terminée (3 jeux filtrés).")


if __name__ == "__main__":
    compute_pearson_filter_multi()

