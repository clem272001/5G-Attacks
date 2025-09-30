import pandas as pd
from sklearn.preprocessing import StandardScaler

def fit_scaler_on_file(file_in, exclude_cols=None, chunksize=50_000, sep=';'):
    print(f"[FIT] Fichier : {file_in}")
    scaler = StandardScaler()
    columns_to_scale = None

    for chunk in pd.read_csv(file_in, chunksize=chunksize, sep=sep):
        if columns_to_scale is None:
            exclude_cols = exclude_cols or []
            columns_to_scale = [col for col in chunk.columns if col not in exclude_cols]
        chunk_to_scale = chunk[columns_to_scale].fillna(0).astype(float)
        scaler.partial_fit(chunk_to_scale)
    return scaler, columns_to_scale

def transform_file_with_scaler(file_in, file_out, scaler, columns_to_scale, exclude_cols=None, chunksize=50_000, sep=';'):
    write_header = True
    for chunk in pd.read_csv(file_in, chunksize=chunksize, sep=sep):
        chunk_to_scale = chunk[columns_to_scale].fillna(0).astype(float)
        scaled = pd.DataFrame(scaler.transform(chunk_to_scale), columns=columns_to_scale, index=chunk.index)

        for col in (exclude_cols or []):
            if col in chunk.columns:
                scaled[col] = chunk[col].values
        scaled.to_csv(file_out, index=False, header=write_header, sep=sep, mode='w' if write_header else 'a')
        write_header = False

if __name__ == "__main__":
    sep = ';'
    chunksize = 50_000
    exclude_att = ["ip.opt.time_stamp", "frame.number", "source_file"]

    scaler, columns_to_scale = fit_scaler_on_file("dataset_1_filtered.csv", exclude_cols=exclude_att, chunksize=chunksize, sep=sep)

    transform_file_with_scaler("dataset_1_filtered.csv", "dataset_1_scaled.csv", scaler, columns_to_scale, exclude_cols=exclude_att, chunksize=chunksize, sep=sep)
    transform_file_with_scaler("dataset_2_filtered.csv", "dataset_2_scaled.csv", scaler, columns_to_scale, exclude_cols=exclude_att, chunksize=chunksize, sep=sep)
    transform_file_with_scaler("dataset_3_filtered.csv", "dataset_3_scaled.csv", scaler, columns_to_scale, exclude_cols=exclude_att, chunksize=chunksize, sep=sep)
