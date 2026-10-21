import pandas as pd
from pathlib import Path

for f in sorted(Path("data/raw").glob("*.csv")):
    df = pd.read_csv(f)
    print(f"{f.name:25s} lignes={len(df)}  manquantes={df.isna().sum().sum()}")