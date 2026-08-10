import pandas as pd
import os

data_folder = "data"
for file in os.listdir(data_folder):
    if file.endswith(".csv"):
        print(f"\n--- {file} ---")
        df = pd.read_csv(os.path.join(data_folder, file), nrows=5)
        print("Columns:", list(df.columns))
        print(df.head())