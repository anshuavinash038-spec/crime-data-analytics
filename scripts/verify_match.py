"""
============================================================
  VERIFICATION SCRIPT: Web Dashboard vs Power BI Data Match
============================================================
Ye script dono sources se numbers nikalti hai aur compare karti hai.
  Source-1: SQLite DB (jaise Web Dashboard padhta hai)
  Source-2: Power BI Excel file (jo Power BI Desktop load karta hai)
"""
import os, sys, sqlite3
import pandas as pd

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE, "database", "crime_analytics.db")
EXCEL_PATH = os.path.join(BASE, "data", "powerbi_crime_dataset.xlsx")

PASS = "✅ MATCH"
FAIL = "❌ MISMATCH"
SEP = "=" * 65

def compare(label, web_val, pbi_val, tolerance=0.01):
    """Compare two values with optional tolerance for floats."""
    if isinstance(web_val, float) or isinstance(pbi_val, float):
        match = abs(float(web_val) - float(pbi_val)) < tolerance
    else:
        match = web_val == pbi_val
    status = PASS if match else FAIL
    print(f"  {status}  {label}")
    print(f"           Web Dashboard : {web_val}")
    print(f"           Power BI Excel: {pbi_val}")
    print()
    return match

def main():
    # ── Check files exist ─────────────────────────────────────────
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        sys.exit(1)
    if not os.path.exists(EXCEL_PATH):
        print(f"❌ Excel file not found: {EXCEL_PATH}")
        print("   Pehle 'python scripts/prepare_powerbi_dataset.py' chala lo!")
        sys.exit(1)

    print(SEP)
    print("  WEB DASHBOARD  vs  POWER BI DESKTOP  — Verification")
    print(SEP)
    print()

    # ══════════════════════════════════════════════════════════════
    # SOURCE 1: SQLite DB (Web Dashboard jaise padhta hai)
    # ══════════════════════════════════════════════════════════════
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    row = conn.execute("""
        SELECT 
            COUNT(*) as total_records,
            COALESCE(SUM(cases_reported), 0) as total_cases,
            COALESCE(SUM(chargesheeted), 0) as total_chargesheeted,
            COALESCE(SUM(convictions), 0) as total_convictions,
            COALESCE(AVG(crime_rate_per_100k), 0.0) as avg_crime_rate
        FROM crime_data
    """).fetchone()

    web_total_records = row["total_records"]
    web_total_cases = row["total_cases"]
    web_total_chg = row["total_chargesheeted"]
    web_total_conv = row["total_convictions"]
    web_avg_rate = round(row["avg_crime_rate"], 2)
    web_chg_rate = round(web_total_chg / web_total_cases * 100, 2) if web_total_cases > 0 else 0.0
    web_conv_rate = round(web_total_conv / web_total_chg * 100, 2) if web_total_chg > 0 else 0.0

    # State-wise from DB
    web_state = pd.read_sql_query("""
        SELECT state, SUM(cases_reported) as total_cases
        FROM crime_data GROUP BY state ORDER BY total_cases DESC
    """, conn)

    # Yearly from DB
    web_yearly = pd.read_sql_query("""
        SELECT year, SUM(cases_reported) as total_cases
        FROM crime_data GROUP BY year ORDER BY year
    """, conn)

    # Crime type from DB
    web_crime = pd.read_sql_query("""
        SELECT crime_type, SUM(cases_reported) as total_cases
        FROM crime_data GROUP BY crime_type ORDER BY total_cases DESC
    """, conn)

    conn.close()

    # ══════════════════════════════════════════════════════════════
    # SOURCE 2: Power BI Excel File
    # ══════════════════════════════════════════════════════════════
    pbi_state = pd.read_excel(EXCEL_PATH, sheet_name="State_Analytics")
    pbi_yearly = pd.read_excel(EXCEL_PATH, sheet_name="Yearly_Trends")
    pbi_crime = pd.read_excel(EXCEL_PATH, sheet_name="Crime_Type_Analytics")

    pbi_total_cases = int(pbi_state["total_cases"].sum())
    pbi_total_chg = int(pbi_state["total_chargesheeted"].sum())
    pbi_total_conv = int(pbi_state["total_convictions"].sum())
    pbi_total_records = int(pbi_state["total_records"].sum())
    pbi_avg_rate = round(pbi_state["avg_crime_rate"].mean(), 2)
    pbi_chg_rate = round(pbi_total_chg / pbi_total_cases * 100, 2) if pbi_total_cases > 0 else 0.0
    pbi_conv_rate = round(pbi_total_conv / pbi_total_chg * 100, 2) if pbi_total_chg > 0 else 0.0

    # ══════════════════════════════════════════════════════════════
    # COMPARE KPIs
    # ══════════════════════════════════════════════════════════════
    results = []
    print("─── KPI CARDS COMPARISON ───────────────────────────────")
    print()
    results.append(compare("Total Records",        web_total_records, pbi_total_records))
    results.append(compare("Total Cases Reported",  web_total_cases,   pbi_total_cases))
    results.append(compare("Total Chargesheeted",   web_total_chg,     pbi_total_chg))
    results.append(compare("Total Convictions",     web_total_conv,    pbi_total_conv))
    results.append(compare("Chargesheet Rate %",    web_chg_rate,      pbi_chg_rate))
    results.append(compare("Conviction Rate %",     web_conv_rate,     pbi_conv_rate))

    # ── Yearly Trends ────────────────────────────────────────────
    print("─── YEARLY TRENDS COMPARISON ──────────────────────────")
    print()
    pbi_yr = pbi_yearly.set_index("year")["total_cases"].to_dict()
    web_yr = web_yearly.set_index("year")["total_cases"].to_dict()
    for yr in sorted(set(list(web_yr.keys()) + list(pbi_yr.keys()))):
        results.append(compare(f"Year {yr}", int(web_yr.get(yr, 0)), int(pbi_yr.get(yr, 0))))

    # ── State-wise Top 5 ─────────────────────────────────────────
    print("─── TOP 5 STATES COMPARISON ───────────────────────────")
    print()
    pbi_st = pbi_state.set_index("state")["total_cases"].to_dict()
    web_st = web_state.set_index("state")["total_cases"].to_dict()
    for state in list(web_state["state"].head(5)):
        results.append(compare(f"State: {state}", int(web_st.get(state, 0)), int(pbi_st.get(state, 0))))

    # ── Crime Type Top 5 ─────────────────────────────────────────
    print("─── TOP 5 CRIME TYPES COMPARISON ──────────────────────")
    print()
    pbi_ct = pbi_crime.set_index("crime_type")["total_cases"].to_dict()
    web_ct = web_crime.set_index("crime_type")["total_cases"].to_dict()
    for ct in list(web_crime["crime_type"].head(5)):
        results.append(compare(f"Crime: {ct}", int(web_ct.get(ct, 0)), int(pbi_ct.get(ct, 0))))

    # ══════════════════════════════════════════════════════════════
    # FINAL VERDICT
    # ══════════════════════════════════════════════════════════════
    print(SEP)
    total = len(results)
    passed = sum(results)
    failed = total - passed
    if failed == 0:
        print(f"  🎉 RESULT: ALL {total} CHECKS PASSED — DONO DASHBOARDS MATCH!")
    else:
        print(f"  ⚠️  RESULT: {passed}/{total} passed, {failed} MISMATCH found!")
    print(SEP)

if __name__ == "__main__":
    main()
