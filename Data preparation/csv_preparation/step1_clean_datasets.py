import pandas as pd

def get_null_and_constant_columns(file_path, chunksize=100_000):
    null_counts = {}
    unique_values = {}

    for chunk in pd.read_csv(file_path, sep=';', chunksize=chunksize, low_memory=False):
        for col in chunk.columns:
            null_counts[col] = null_counts.get(col, 0) + chunk[col].isna().sum()
            if col not in unique_values:
                unique_values[col] = set()
            unique_values[col].update(chunk[col].dropna().unique())
    return null_counts, unique_values

def get_columns_to_drop(nulls1, uniques1, total1, nulls2, uniques2, total2, nulls3, uniques3, total3):
    cols_to_drop = []
    for col in set(nulls1.keys()).union(nulls2.keys()).union(nulls3.keys()):
        is_null_in_all = (
            nulls1.get(col, total1) == total1 and
            nulls2.get(col, total2) == total2 and
            nulls3.get(col, total3) == total3
        )
        is_constant_in_all = (
            len(uniques1.get(col, set())) <= 1 and
            len(uniques2.get(col, set())) <= 1 and
            len(uniques3.get(col, set())) <= 1
        )
        if is_null_in_all or is_constant_in_all:
            reason = "null" if is_null_in_all else "constant"
            #print(f"{col} (dropped because {reason})")
            cols_to_drop.append(col)
    
    return cols_to_drop

def clean_and_save(input_path, output_path, columns_to_drop, chunksize=100_000):
    write_header = True
    for chunk in pd.read_csv(input_path, sep=';', chunksize=chunksize, low_memory=False):
        chunk = chunk.drop(columns=[col for col in columns_to_drop if col in chunk.columns])
        chunk.to_csv(output_path, sep=';', index=False, mode='w' if write_header else 'a', header=write_header)
        write_header = False

# === STEP 1: analyser les trois datasets ===
file1 = "dataset_1.csv"
file2 = "dataset_2.csv"
file3 = "dataset_3.csv"

nulls1, uniques1 = get_null_and_constant_columns(file1)
nulls2, uniques2 = get_null_and_constant_columns(file2)
nulls3, uniques3 = get_null_and_constant_columns(file3)

total_rows_1 = sum(1 for _ in open(file1)) - 1
total_rows_2 = sum(1 for _ in open(file2)) - 1
total_rows_3 = sum(1 for _ in open(file3)) - 1

cols_to_drop = get_columns_to_drop(nulls1, uniques1, total_rows_1,
                                   nulls2, uniques2, total_rows_2,
                                   nulls3, uniques3, total_rows_3)
print('Col to drop len : ', len(cols_to_drop))

# === STEP 2: enregistrer les versions nettoyées ===
clean_and_save(file1, "dataset_1_cleaned.csv", cols_to_drop)
clean_and_save(file2, "dataset_2_cleaned.csv", cols_to_drop)
clean_and_save(file3, "dataset_3_cleaned.csv", cols_to_drop)
