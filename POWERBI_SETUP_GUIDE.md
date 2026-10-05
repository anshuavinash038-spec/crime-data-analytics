# Microsoft Power BI Desktop - Crime Analytics Integration & Visualization Guide

This project includes complete integration with **Microsoft Power BI Desktop (x64)**. The dataset is directly synchronized with the project's official SQLite database (`database/crime_analytics.db`) covering **all 28 States, 743 LGD Districts, and 252,240 records (2021–2025)**.

---

## 🚀 Quick Start (1-Click)

Simply double-click:
```
Launch_PowerBI_Dashboard.bat
```
This batch script automatically:
1. Refreshes the Power BI datasets from the active SQLite database.
2. Opens File Explorer highlighting `data/powerbi_crime_dataset.xlsx`.
3. Launches **Microsoft Power BI Desktop**.

---

## 📊 Pre-Built Dataset Structure

The generated workbook `data/powerbi_crime_dataset.xlsx` contains pre-aggregated, ready-to-visualize sheets:

| Sheet Name | Description | Key Fields |
| :--- | :--- | :--- |
| **`State_Analytics`** | State-level totals across all 28 states | `state`, `total_cases`, `total_chargesheeted`, `total_convictions`, `avg_crime_rate`, `chargesheet_rate_pct`, `conviction_rate_pct` |
| **`District_Analytics`** | District-level totals across all 743 districts | `state`, `district`, `total_cases`, `total_chargesheeted`, `total_convictions`, `avg_crime_rate`, `chargesheet_rate_pct`, `conviction_rate_pct` |
| **`Crime_Type_Analytics`** | Breakdown across all 12 IPC Crime Categories | `crime_type`, `total_cases`, `pct_of_total_crime`, `total_chargesheeted`, `total_convictions`, `conviction_rate_pct` |
| **`Yearly_Trends`** | Year-over-year progression (2021–2025) | `year`, `total_cases`, `total_chargesheeted`, `total_convictions`, `avg_crime_rate`, `yoy_growth_pct` |
| **`Crime_Data_Sample`** | Granular incident-level records | `state`, `district`, `area`, `year`, `crime_type`, `cases_reported`, `chargesheeted`, `convictions`, `population`, `crime_rate_per_100k` |
| **`DAX_Measures_Reference`** | Complete DAX formulas cheat sheet | Measure names, exact formulas, and viva descriptions |

*(For full granular incident analysis with all 252,240 rows, you can also load `data/powerbi_full_crime_data.csv`).*

---

## 🎨 Recommended Graphs to Build in Power BI Desktop (Step-by-Step)

Once you click **Get Data → Excel workbook** and load the sheets:

### 1. KPI Summary Cards (Top Row)
- **Visual Type**: `Card`
- **Fields**:
  - Card 1: `State_Analytics[total_cases]` (Title: *Total Cases Reported*)
  - Card 2: `State_Analytics[total_chargesheeted]` (Title: *Total Chargesheeted*)
  - Card 3: `State_Analytics[total_convictions]` (Title: *Total Convictions*)
  - Card 4: `State_Analytics[conviction_rate_pct]` (Average, Title: *Overall Conviction Rate %*)

### 2. Crime Distribution by Crime Type (Top Right)
- **Visual Type**: `Donut Chart` or `Pie Chart`
- **Legend**: `Crime_Type_Analytics[crime_type]`
- **Values**: `Crime_Type_Analytics[total_cases]`
- **Insight**: Displays the proportional share of Theft, Cybercrime, Murder, Fraud, Assault, etc.

### 3. State-wise Crime Ranking (Left / Center)
- **Visual Type**: `Clustered Bar Chart`
- **Y-Axis**: `State_Analytics[state]`
- **X-Axis**: `State_Analytics[total_cases]` and `State_Analytics[total_chargesheeted]`
- **Insight**: Compares total reported incidents against police investigation chargesheets across States.

### 4. 5-Year Crime Trend (Bottom Center)
- **Visual Type**: `Line and Clustered Column Chart` or `Area Chart`
- **X-Axis**: `Yearly_Trends[year]`
- **Column values / Line values**: `Yearly_Trends[total_cases]` and `Yearly_Trends[total_convictions]`
- **Insight**: Visualizes crime trajectory and justice outcomes from 2021 through 2025.

### 5. District Drilldown Matrix (Bottom Full Width)
- **Visual Type**: `Matrix`
- **Rows**: `District_Analytics[state]`, `District_Analytics[district]`
- **Values**: `total_cases`, `total_chargesheeted`, `total_convictions`, `avg_crime_rate`
- **Insight**: Enables expandable drill-down from State into individual Districts (e.g. Uttar Pradesh → Pratapgarh, Ayodhya, Jhansi, etc.).

### 6. Interactive Slicers (Filters)
- **Visual Type**: `Slicer`
- **Fields**:
  - Slicer 1: `Yearly_Trends[year]` (Dropdown or buttons for 2021, 2022, 2023, 2024, 2025)
  - Slicer 2: `State_Analytics[state]` (Searchable dropdown)

---

## 🧮 DAX Measures Reference (Copy-Paste Ready)

Click **Modeling → New Measure** and paste any of the following formulas:

```dax
Total Crimes = SUM('Crime_Data_Sample'[cases_reported])
```

```dax
Total Chargesheeted = SUM('Crime_Data_Sample'[chargesheeted])
```

```dax
Total Convictions = SUM('Crime_Data_Sample'[convictions])
```

```dax
Chargesheet Rate % = DIVIDE([Total Chargesheeted], [Total Crimes], 0) * 100
```

```dax
Conviction Rate % = DIVIDE([Total Convictions], [Total Chargesheeted], 0) * 100
```

```dax
Average Crime Rate = AVERAGE('Crime_Data_Sample'[crime_rate_per_100k])
```

---

## 🌐 Web Portal Integration
The Flask web application also features a dedicated **Power BI Intelligence Center** page at:
- **URL**: `http://127.0.0.1:5000/powerbi`
- Provides an in-app Power BI simulated UI, instant CSV/Excel dataset downloads, and allows live iFrame embedding if you publish your report to Power BI Service (`app.powerbi.com`).
