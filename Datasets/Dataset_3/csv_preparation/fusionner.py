import pandas as pd
import glob
import os

csv_files = [f for f in glob.glob("*.csv") if not f.startswith("merged_dataset")]

# Open output CSV file and write header from the first file
with open("merged_dataset.csv", "w", encoding='utf-8') as outfile:
    # Write header from the first file
    first_file = True
    for file in csv_files:
        filename = os.path.basename(file)
        print(filename)
        for chunk in pd.read_csv(file, sep=';', chunksize=100000    , low_memory=False,quoting=3):  # read in chunks
            #chunk["source_file"] = filename 
            if first_file:
                chunk.to_csv(outfile, sep=';', index=False, header=True, mode='a')
                first_file = False
            else:
                chunk.to_csv(outfile, sep=';', index=False, header=False, mode='a')
