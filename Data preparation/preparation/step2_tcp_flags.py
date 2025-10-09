import pandas as pd

def enrich_tcp_columns(input_file, output_file, chunksize=100_000):
    write_header = True
    for chunk in pd.read_csv(input_file, sep=';', chunksize=chunksize, low_memory=False):
        if 'tcp.options' in chunk.columns:
            chunk['tcp.options'] = chunk['tcp.options'].fillna('')
            chunk['tcp_opt_mss'] = chunk['tcp.options'].str.contains('mss', case=False).astype(int)
            chunk['tcp_opt_ts'] = chunk['tcp.options'].str.contains('timestamp', case=False).astype(int)
            chunk['tcp_opt_sack'] = chunk['tcp.options'].str.contains('sack', case=False).astype(int)
            chunk['tcp_opt_wscale'] = chunk['tcp.options'].str.contains('wscale', case=False).astype(int)
            chunk = chunk.drop(columns=['tcp.options'], errors='ignore')
        chunk.to_csv(output_file, sep=';', index=False, mode='w' if write_header else 'a', header=write_header)
        write_header = False

enrich_tcp_columns("dataset_1_cleaned.csv", "dataset_1_tcp.csv")
enrich_tcp_columns("dataset_2_cleaned.csv", "dataset_2_tcp.csv")
enrich_tcp_columns("dataset_3_cleaned.csv", "dataset_3_tcp.csv")
