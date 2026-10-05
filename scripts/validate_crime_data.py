import os
import sys
import pandas as pd
import numpy as np

def validate():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    csv_path = os.path.join(base_dir, "data", "sample_crime_data.csv")

    print(f"Loading crime dataset from: {csv_path}")
    df = pd.read_csv(csv_path)

    total_rows = len(df)
    print(f"Total Rows: {total_rows:,}")
    print(f"Columns: {list(df.columns)}")

    # 1. Null / Missing Checks
    null_counts = df.isnull().sum().to_dict()
    print("\n--- 1. Missing Values per Column ---")
    for col, count in null_counts.items():
        print(f"  {col}: {count} ({count/total_rows*100:.2f}%)")

    # 2. Duplicate Checks
    subset_cols = ["state", "district", "area", "year", "crime_type"]
    dupes = df.duplicated(subset=subset_cols).sum()
    print(f"\n--- 2. Duplicate Rows (on state, dist, area, year, crime_type): {dupes} ---")

    # 3. Numeric Types and Bounds
    numeric_cols = ["cases_reported", "chargesheeted", "convictions", "population", "crime_rate_per_100k"]
    print("\n--- 3. Negative Counts & Out-of-Bound Values ---")
    for col in numeric_cols:
        neg_count = (df[col] < 0).sum()
        print(f"  {col} < 0: {neg_count}")

    # 4. Year Validity
    years = sorted(df["year"].unique().tolist())
    print(f"\n--- 4. Years in Dataset ---: {years}")

    # 5. Distinct States and Distinct Crime Types
    states = sorted(df["state"].unique().tolist())
    crime_types = sorted(df["crime_type"].unique().tolist())
    print(f"\n--- 5. Distinct States ({len(states)}) ---")
    print(", ".join(states[:10]) + f"... (+{len(states)-10} more)")
    print(f"\n--- 6. Distinct Crime Types ({len(crime_types)}) ---")
    print(", ".join(crime_types))

    # 6. Logical Relational Bounds Check
    conv_gt_charge = (df["convictions"] > df["chargesheeted"]).sum()
    print(f"\n--- 7. Convictions > Chargesheeted Anomalies: {conv_gt_charge} ---")

    # 7. Crime Rate Computation Check
    expected_rate = (df["cases_reported"] / df["population"].replace(0, np.nan) * 100000).round(2)
    rate_diff = np.abs(df["crime_rate_per_100k"].round(2) - expected_rate).fillna(0)
    rate_mismatch = (rate_diff > 0.05).sum()
    print(f"--- 8. Crime Rate Computation Variance (>0.05 mismatch): {rate_mismatch} ({rate_mismatch/total_rows*100:.2f}%) ---")

    print("\nValidation script finished successfully!")

if __name__ == "__main__":
    validate()
