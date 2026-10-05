import os
import sqlite3
import pandas as pd

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    db_path = os.path.join(base_dir, "database", "crime_analytics.db")
    excel_path = os.path.join(base_dir, "data", "powerbi_crime_dataset.xlsx")
    full_csv_path = os.path.join(base_dir, "data", "powerbi_full_crime_data.csv")

    print(f"Loading data from database: {db_path}")
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        query = """
            SELECT state, district, area, year, crime_type, 
                   cases_reported, chargesheeted, convictions, 
                   population, crime_rate_per_100k 
            FROM crime_data
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        print(f"Loaded {len(df):,} records from database across all 28 states and 743 districts.")
    else:
        csv_path = os.path.join(base_dir, "data", "sample_crime_data.csv")
        print(f"Fallback: reading from {csv_path}")
        df = pd.read_csv(csv_path)

    # Export full CSV for high-scale Power BI loading
    print(f"Writing complete dataset CSV to: {full_csv_path}")
    df.to_csv(full_csv_path, index=False, encoding='utf-8')

    # 1. State Analytics Summary (All 28 States)
    state_df = df.groupby("state").agg(
        total_cases=('cases_reported', 'sum'),
        total_chargesheeted=('chargesheeted', 'sum'),
        total_convictions=('convictions', 'sum'),
        avg_crime_rate=('crime_rate_per_100k', 'mean'),
        total_records=('cases_reported', 'count')
    ).reset_index()
    state_df['chargesheet_rate_pct'] = (state_df['total_chargesheeted'] / state_df['total_cases'].replace(0, 1) * 100).round(2)
    state_df['conviction_rate_pct'] = (state_df['total_convictions'] / state_df['total_chargesheeted'].replace(0, 1) * 100).round(2)
    state_df['avg_crime_rate'] = state_df['avg_crime_rate'].round(2)
    state_df = state_df.sort_values(by="total_cases", ascending=False)

    # 2. District Analytics (Aggregated by State and District)
    district_df = df.groupby(["state", "district"]).agg(
        total_cases=('cases_reported', 'sum'),
        total_chargesheeted=('chargesheeted', 'sum'),
        total_convictions=('convictions', 'sum'),
        avg_crime_rate=('crime_rate_per_100k', 'mean')
    ).reset_index()
    district_df['chargesheet_rate_pct'] = (district_df['total_chargesheeted'] / district_df['total_cases'].replace(0, 1) * 100).round(2)
    district_df['conviction_rate_pct'] = (district_df['total_convictions'] / district_df['total_chargesheeted'].replace(0, 1) * 100).round(2)
    district_df['avg_crime_rate'] = district_df['avg_crime_rate'].round(2)
    district_df = district_df.sort_values(by="total_cases", ascending=False)

    # 3. Crime Type Summary
    crime_df = df.groupby("crime_type").agg(
        total_cases=('cases_reported', 'sum'),
        total_chargesheeted=('chargesheeted', 'sum'),
        total_convictions=('convictions', 'sum'),
        avg_crime_rate=('crime_rate_per_100k', 'mean')
    ).reset_index()
    crime_df['pct_of_total_crime'] = (crime_df['total_cases'] / crime_df['total_cases'].sum() * 100).round(2)
    crime_df['conviction_rate_pct'] = (crime_df['total_convictions'] / crime_df['total_chargesheeted'].replace(0, 1) * 100).round(2)
    crime_df = crime_df.sort_values(by="total_cases", ascending=False)

    # 4. Yearly Trends (2021-2025)
    year_df = df.groupby("year").agg(
        total_cases=('cases_reported', 'sum'),
        total_chargesheeted=('chargesheeted', 'sum'),
        total_convictions=('convictions', 'sum'),
        avg_crime_rate=('crime_rate_per_100k', 'mean')
    ).reset_index().sort_values(by="year")
    year_df['chargesheet_rate_pct'] = (year_df['total_chargesheeted'] / year_df['total_cases'].replace(0, 1) * 100).round(2)
    year_df['conviction_rate_pct'] = (year_df['total_convictions'] / year_df['total_chargesheeted'].replace(0, 1) * 100).round(2)
    year_df['yoy_growth_pct'] = year_df['total_cases'].pct_change().fillna(0).mul(100).round(2)

    # 5. DAX Measures Reference Table for Power BI Desktop
    dax_data = [
        {"Measure Name": "Total Crimes Reported", "DAX Formula": "Total Crimes = SUM(Crime_Data[cases_reported])", "Description": "Calculates total reported incidents across any selected filters (State, District, Year, Crime Type)"},
        {"Measure Name": "Total Chargesheeted", "DAX Formula": "Total Chargesheeted = SUM(Crime_Data[chargesheeted])", "Description": "Calculates total cases where police completed investigation and filed chargesheet"},
        {"Measure Name": "Total Convictions", "DAX Formula": "Total Convictions = SUM(Crime_Data[convictions])", "Description": "Calculates judicial convictions obtained"},
        {"Measure Name": "Chargesheet Rate %", "DAX Formula": "Chargesheet Rate % = DIVIDE([Total Chargesheeted], [Total Crimes], 0) * 100", "Description": "Measures police investigation completion efficiency"},
        {"Measure Name": "Conviction Rate %", "DAX Formula": "Conviction Rate % = DIVIDE([Total Convictions], [Total Chargesheeted], 0) * 100", "Description": "Measures judicial prosecution success rate"},
        {"Measure Name": "Average Crime Rate", "DAX Formula": "Avg Crime Rate = AVERAGE(Crime_Data[crime_rate_per_100k])", "Description": "Average annual crime rate per 100,000 population"}
    ]
    dax_df = pd.DataFrame(dax_data)

    # 6. Sample Granular Records (First 10,000 rows for speedy Excel handling)
    sample_df = df.head(10000)

    # Write multi-sheet Excel file optimized for Power BI
    print(f"Writing Power BI Multi-Sheet Excel Workbook to: {excel_path}")
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        state_df.to_excel(writer, sheet_name="State_Analytics", index=False)
        district_df.to_excel(writer, sheet_name="District_Analytics", index=False)
        crime_df.to_excel(writer, sheet_name="Crime_Type_Analytics", index=False)
        year_df.to_excel(writer, sheet_name="Yearly_Trends", index=False)
        sample_df.to_excel(writer, sheet_name="Crime_Raw_Data", index=False)
        dax_df.to_excel(writer, sheet_name="DAX_Measures_Reference", index=False)

    print("Successfully generated all Power BI datasets (Excel & CSV)!")

if __name__ == "__main__":
    main()
