import pandas as pd

input_jeu1 = "dataset_1_tcp.csv"
input_jeu2 = "dataset_2_tcp.csv"
input_jeu3 = "dataset_3_tcp.csv"
output_jeu1 = "dataset_1_drop.csv"
output_jeu2 = "dataset_2_drop.csv"
output_jeu3 = "dataset_3_drop.csv"

columns_to_delete = [
    'ip.hdr_len','ip.len','tcp.payload','tcp.segment_data',
    'tcp.reassembled.data','ip.id','ip.checksum','udp.payload','source_file','frame.number'
]
chunksize = 100_000

def drop_columns_chunked(input_file, output_file, is_attack=False):
    write_header = True
    for chunk in pd.read_csv(input_file, sep=';', chunksize=chunksize, low_memory=False):
        cols_to_drop = [col for col in columns_to_delete if col in chunk.columns]
        chunk.drop(columns=cols_to_drop, inplace=True)

        if 'pfcp.seid' in chunk.columns:
            chunk['pfcp.seid'] = chunk['pfcp.seid'].apply(
                lambda x: int(str(x), 16) if pd.notnull(x) and str(x).startswith("0x") else pd.to_numeric(x, errors='coerce')
            )
        if 'pfcp.f_teid.teid' in chunk.columns:
            chunk['pfcp.f_teid.teid'] = chunk['pfcp.f_teid.teid'].apply(
                lambda x: int(str(x), 16) if pd.notnull(x) and str(x).startswith("0x") else pd.to_numeric(x, errors='coerce')
            )
        chunk.to_csv(output_file, sep=';', index=False, mode='w' if write_header else 'a', header=write_header)
        write_header = False

drop_columns_chunked(input_jeu1, output_jeu1, is_attack=False)
drop_columns_chunked(input_jeu2, output_jeu2, is_attack=True)
drop_columns_chunked(input_jeu3, output_jeu3, is_attack=True)

print("Étape 3 terminée.")
