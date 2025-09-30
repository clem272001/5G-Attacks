import pandas as pd
from sklearn.impute import SimpleImputer

chunksize = 100000
exclude_cols = ["ip.opt.time_stamp", "frame.number", "source_file"]

def compute_numerical_medians(file_path):
    numerics = None
    collected_chunks = []

    for chunk in pd.read_csv(file_path, sep=';', chunksize=chunksize, low_memory=False):
        numeric_cols = chunk.select_dtypes(include='number').columns.tolist()
        numeric_cols = [col for col in numeric_cols if col not in exclude_cols]

        if numerics is None:
            numerics = numeric_cols
        collected_chunks.append(chunk[numeric_cols])

    full_df = pd.concat(collected_chunks, axis=0)
    valid_cols = full_df.columns[full_df.notna().any()].tolist()
    full_df = full_df[valid_cols]

    imputer = SimpleImputer(strategy='median')
    imputer.fit(full_df)

    return valid_cols, imputer

def impute_file(input_file, output_file, valid_cols, imputer):
    write_header = True

    for chunk in pd.read_csv(input_file, sep=';', chunksize=chunksize, low_memory=False):
        excluded_data = {col: chunk[col] for col in exclude_cols if col in chunk.columns}

        chunk_numeric = chunk[valid_cols]
        chunk_imputed = pd.DataFrame(imputer.transform(chunk_numeric), columns=valid_cols, index=chunk.index)

        for col, data in excluded_data.items():
            chunk_imputed[col] = data

        other_cols = [c for c in chunk.columns if c not in valid_cols and c not in exclude_cols]
        final_chunk = pd.concat([
            chunk_imputed.reset_index(drop=True),
            chunk[other_cols].reset_index(drop=True)
        ], axis=1)

        final_chunk.to_csv(output_file, sep=';', index=False, mode='w' if write_header else 'a', header=write_header)
        write_header = False

    print(f"Imputation terminée : {input_file} → {output_file}")

# Main
print("Calcul des médianes sur 'saine'...")
saine_cols, saine_imputer = compute_numerical_medians("dataset_1_drop.csv")
impute_file("dataset_1_drop.csv", "dataset_1_imputed.csv", saine_cols, saine_imputer)

print("Calcul des médianes sur 'attack'...")
attack_cols, attack_imputer = compute_numerical_medians("dataset_2_drop.csv")
impute_file("dataset_2_drop.csv", "dataset_2_imputed.csv", attack_cols, attack_imputer)

print("Calcul des médianes sur 'dataset_3' (comme attack)...")
impute_file("dataset_3_drop.csv", "dataset_3_imputed.csv", attack_cols, attack_imputer)
