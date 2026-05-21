import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from scipy import stats
from pathlib import Path

def read_raw_data(ref_path: Path):
    if not ref_path.exists():
        raise FileNotFoundError(f'Не найден справочник: {ref_path}')
    
    ref_df = pd.read_csv(ref_path, encoding="utf-8")
    
    return ref_df
    
if __name__ == "__main__":
    ref_path = Path(__file__).parent.parent / "raw_data" / "customer_data.csv"
    
    df = read_raw_data(ref_path)
    print(df.head(10))