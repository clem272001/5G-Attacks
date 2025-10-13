import pandas as pd
from sklearn.preprocessing import OneHotEncoder
import os

# Fichiers d'entrée / sortie
input_attack = "dataset_2_imputed.csv"
output_attack = "dataset_2_encoded.csv"
input_saine = "dataset_1_imputed.csv"
output_saine = "dataset_1_encoded.csv"
input_attack2 = "dataset_3_imputed.csv"
output_attack2 = "dataset_3_encoded.csv"

# Colonnes à frequency encoder
freq_cols = [
    'ip.src_host','ip.dst_host','ip.host','ip.addr','ip.src', 'ip.dst',
    'tcp.srcport', 'tcp.dstport','udp.srcport', 'udp.dstport',
    'pfcp.node_id_ipv4','pfcp.outer_hdr_creation.ipv4',
    'pfcp.f_teid.ipv4_addr','pfcp.f_seid.ipv4',
    'pfcp.outer_hdr_creation.teid','pfcp.ue_ip_addr_ipv4','tcp.checksum','udp.checksum'
]

# Colonnes time à convertir
time_columns = [
    'pfcp.time_of_first_packet', 'pfcp.time_of_last_packet',
    'pfcp.end_time', 'pfcp.recovery_time_stamp'
]

# Colonnes spéciales (à supprimer ou garder à part)
special_columns = ['ip.opt.time_stamp']

# Fonction de frequency encoding
def frequency_encode(df, col):
    freq = df[col].value_counts()
    encoding = freq.rank(method='dense', ascending=False).astype(int)
    return df[col].map(encoding)

# Conversion des colonnes temps
def time_conversion(df, col):
    df[col] = pd.to_datetime(
        df[col],
        format='%b %d, %Y %H:%M:%S.%f %Z',
        errors='coerce'
    )
    df[col] = df[col].astype('int64') // 10**9
    return df[col]

### Étape 1 : Frequency encoding et préparation ###
print("\n== Étape 1 : Frequency encoding ==")
df_attack = pd.read_csv(input_attack, sep=';', low_memory=False)
df_saine = pd.read_csv(input_saine, sep=';', low_memory=False)
df_attack2 = pd.read_csv(input_attack2, sep=';', low_memory=False)

non_num_attack = df_attack.select_dtypes(include=['object']).columns.tolist()
non_num_saine = df_saine.select_dtypes(include=['object']).columns.tolist()
non_num_attack2 = df_attack2.select_dtypes(include=['object']).columns.tolist()

non_num_cols = sorted(set(non_num_attack).union(set(non_num_saine)).union(set(non_num_attack2)))

# Nettoyage : on retire les colonnes déjà frequency-encodées, spéciales et temporelles
non_num_cols = [col for col in non_num_cols if col not in freq_cols and col not in special_columns and col not in time_columns]

# forcer la conversion des colonnes object qui sont en réalité numériques
fake_num_cols = []
for col in list(non_num_cols):
    try:
        converted = pd.to_numeric(df_attack[col], errors='coerce')
        if converted.notna().sum() > 0 and converted.nunique() > 1:
            fake_num_cols.append(col)
            for df_tmp in [df_attack, df_saine, df_attack2]:
                if col in df_tmp.columns:
                    df_tmp[col] = pd.to_numeric(df_tmp[col], errors='coerce')
            non_num_cols.remove(col)
    except Exception:
        pass

if fake_num_cols:
    print("Colonnes object recastées en numériques :", fake_num_cols)

print("=> Préparation du OneHotEncoder global...")
df_attack_cat = df_attack[non_num_cols]
df_saine_cat = df_saine[non_num_cols]
df_attack2_cat = df_attack2[non_num_cols]

df_cat_all = pd.concat([df_attack_cat, df_saine_cat, df_attack2_cat], axis=0)
encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
encoder.fit(df_cat_all[non_num_cols])

del non_num_attack, non_num_saine, non_num_attack2, df_attack_cat, df_saine_cat, df_attack2_cat, df_cat_all

### Boucle traitement attack/saine/attack2
data_frames = ['df_attack','df_saine','df_attack2']
for data_frame in data_frames:
    if data_frame == 'df_attack':
        df = df_attack
        timestamp_col = df[special_columns[0]] if special_columns[0] in df else None
        if special_columns[0] in df:
            df = df.drop(columns=[special_columns[0]])
    elif data_frame == 'df_saine':
        df = df_saine.copy()
        timestamp_col = None
    else:  # df_attack2
        df = df_attack2
        timestamp_col = df[special_columns[0]] if special_columns[0] in df else None
        if special_columns[0] in df:
            df = df.drop(columns=[special_columns[0]])

    print("--> Frequency encoding des colonnes :")
    for col in freq_cols:
        if col in df.columns:
            print(f"   {data_frame }: {col}")
            df[col] = frequency_encode(df, col)
    
    df_freq_cols = df[[c for c in freq_cols if c in df.columns]]
    
    print("--> Time conversion:")
    for col in time_columns:
        if col in df.columns:
            print(f"    {data_frame}: {col}")
            df[col] = time_conversion(df,col)
    df_time_columns = df[[c for c in time_columns if c in df.columns]]
    df = df[[col for col in df.columns if col not in freq_cols and col not in time_columns]]

    print(f"Colonnes catégorielles à encoder : {len(non_num_cols)}")
    df[non_num_cols] = df[non_num_cols].fillna("NaN").astype(str)

    df_encoded = pd.DataFrame(
        encoder.transform(df[non_num_cols]),
        columns=encoder.get_feature_names_out(non_num_cols)
    )

    df = df.drop(columns=non_num_cols).reset_index(drop=True)
    print('print df.columns: ',df.columns)
    print("Sauvegarde finale des fichiers avec colonnes spéciales...")

    df.to_csv('df_main.csv', sep=';', index=False)
    df_freq_cols.to_csv('df_freq.csv', sep=';', index=False)
    df_encoded.to_csv('df_encoded.csv', sep=';', index=False)
    df_time_columns.to_csv('df_time_columns.csv', sep=';', index=False)

    del df, df_freq_cols, df_encoded, df_time_columns

    chunk_size = 100_000
    if data_frame == 'df_attack':
        if timestamp_col is not None:
            timestamp_col.to_csv('df_timestamp.csv', sep=';', index=False)
        header_written = False
        with open(output_attack, 'w') as f_out:
            for parts in zip(
                pd.read_csv('df_main.csv', sep=';', chunksize=chunk_size),
                pd.read_csv('df_freq.csv', sep=';', chunksize=chunk_size),
                pd.read_csv('df_encoded.csv', sep=';', chunksize=chunk_size),
                (pd.read_csv('df_timestamp.csv', sep=';', chunksize=chunk_size) if timestamp_col is not None else [pd.DataFrame()]),
                pd.read_csv('df_time_columns.csv', sep=';', chunksize=chunk_size),
            ):
                merged = pd.concat([p for p in parts if not p.empty], axis=1)
                merged.to_csv(f_out, sep=';', index=False, header=not header_written)
                header_written = True
    elif data_frame == 'df_saine':
        header_written = False
        with open(output_saine, 'w') as f_out:
            for parts in zip(
                pd.read_csv('df_main.csv', sep=';', chunksize=chunk_size),
                pd.read_csv('df_freq.csv', sep=';', chunksize=chunk_size),
                pd.read_csv('df_encoded.csv', sep=';', chunksize=chunk_size),
                pd.read_csv('df_time_columns.csv', sep=';', chunksize=chunk_size),
            ):
                merged = pd.concat([p for p in parts if not p.empty], axis=1)
                merged.to_csv(f_out, sep=';', index=False, header=not header_written)
                header_written = True
    else:  # df_attack2
        if timestamp_col is not None:
            timestamp_col.to_csv('df_timestamp.csv', sep=';', index=False)
        header_written = False
        with open(output_attack2, 'w') as f_out:
            for parts in zip(
                pd.read_csv('df_main.csv', sep=';', chunksize=chunk_size),
                pd.read_csv('df_freq.csv', sep=';', chunksize=chunk_size),
                pd.read_csv('df_encoded.csv', sep=';', chunksize=chunk_size),
                (pd.read_csv('df_timestamp.csv', sep=';', chunksize=chunk_size) if timestamp_col is not None else [pd.DataFrame()]),
                pd.read_csv('df_time_columns.csv', sep=';', chunksize=chunk_size),
            ):
                merged = pd.concat([p for p in parts if not p.empty], axis=1)
                merged.to_csv(f_out, sep=';', index=False, header=not header_written)
                header_written = True

    for temp_file in ['df_main.csv', 'df_freq.csv', 'df_encoded.csv',
                      'df_timestamp.csv','df_time_columns.csv']:
        try:
            os.remove(temp_file)
        except FileNotFoundError:
            pass

print("\nÉtape 5 terminée.")

