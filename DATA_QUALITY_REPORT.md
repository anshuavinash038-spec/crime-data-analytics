# DATA QUALITY REPORT — Crime Data Analytics & Visualization
**Date:** 2026-10-04

---

## Database Summary (Verified from SQLite)

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
| Crime Records | 2,52,240 | 2,52,240 | OK |
| States | 28 | 28 | OK |
| Districts | 743 | 740 | Minor mismatch |
| Areas (Sub-districts) | 4,204 | 4,125 | Minor mismatch |
| Year Range | 2021-2025 | 2021-2025 | OK |
| NULL cases_reported | 0 | 0 | OK |
| Negative cases_reported | 0 | 0 | OK |

Note: District/Area counts slightly lower than expected — likely due to consolidation or naming differences in source CSV.

---

## KPI Values (Actual from DB — Not Estimated)

| KPI | Value | Formula |
|-----|-------|---------|
| Total Reported Crimes | 86,94,417 | SUM(cases_reported) |
| Total Chargesheeted | 67,38,004 | SUM(chargesheeted) |
| Total Convictions | 37,10,521 | SUM(convictions) |
| Chargesheet Rate | 77.50% | chargesheeted / cases_reported * 100 |
| Conviction Rate | 55.07% | convictions / chargesheeted * 100 |
| Avg Crime Rate | 19.14 per 100k | AVG(crime_rate_per_100k) |

---

## Yearly Breakdown

| Year | Total Cases |
|------|------------|
| 2021 | 16,00,204 |
| 2022 | 16,70,628 |
| 2023 | 17,38,898 |
| 2024 | 18,07,403 |
| 2025 | 18,77,284 |

---

## Top 5 States by Crime Volume

| Rank | State | Total Cases |
|------|-------|------------|
| 1 | Rajasthan | 8,27,111 |
| 2 | Madhya Pradesh | 8,06,253 |
| 3 | Uttar Pradesh | 7,26,863 |
| 4 | Tamil Nadu | 7,14,352 |
| 5 | Maharashtra | 6,97,838 |

---

## Top 5 Crime Types by Volume

| Rank | Crime Type | Total Cases |
|------|-----------|------------|
| 1 | Theft | 24,34,899 |
| 2 | Vehicle Theft | 15,64,390 |
| 3 | Burglary | 10,42,691 |
| 4 | Assault | 8,69,436 |
| 5 | Domestic Violence | 7,82,910 |

---

## Power BI vs Web Dashboard Match

Verified using scripts/verify_match.py:

| Check | Web Dashboard | Power BI Excel | Match |
|-------|-------------|----------------|-------|
| Total Records | 2,52,240 | 2,52,240 | YES |
| Total Cases | 86,94,417 | 86,94,417 | YES |
| Total Chargesheeted | 67,38,004 | 67,38,004 | YES |
| Total Convictions | 37,10,521 | 37,10,521 | YES |
| Chargesheet Rate | 77.50% | 77.50% | YES |
| Conviction Rate | 55.07% | 55.07% | YES |
| Year 2021-2025 | Checked | Checked | YES |
| Top 5 States | Checked | Checked | YES |
| Top 5 Crime Types | Checked | Checked | YES |

All 21 checks PASSED — 100% data consistency.

---

## Data Limitations

1. Avg Crime Rate in Web (19.14) differs from Power BI original (47.27) — Power BI was using a different/older dataset before refresh.
2. Area count (4,125) vs expected (4,204) — 79 areas may be missing from source CSV or merged during data prep.
3. District count (740) vs expected (743) — 3 districts may have naming variants.
4. This is synthetic/generated training data based on realistic Indian crime patterns — not actual NCRB data.

---

## Calculation Definitions (Single Source of Truth)

| Metric | Definition |
|--------|-----------|
| Total Reported Crimes | SUM of cases_reported across selected filters |
| Total Chargesheeted | SUM of chargesheeted — cases where police completed investigation |
| Total Convictions | SUM of convictions — cases with judicial conviction |
| Chargesheet Rate | total_chargesheeted / total_cases * 100 |
| Conviction Rate | total_convictions / total_chargesheeted * 100 |
| Average Crime Rate | AVG of crime_rate_per_100k (already pre-calculated per record) |

These same definitions are used in:
- Flask: `CrimeModel.get_summary_stats()` in `models/crime_model.py`
- Power BI: `DAX_Measures_Reference` sheet in `data/powerbi_crime_dataset.xlsx`
