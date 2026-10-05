"""
==========================================================
  VISUAL COMPARISON: Web Dashboard vs Power BI Data Graphs
==========================================================
Dono sources se charts banake side-by-side save karta hai.
"""
import os, sys, sqlite3
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE, "database", "crime_analytics.db")
EXCEL_PATH = os.path.join(BASE, "data", "powerbi_crime_dataset.xlsx")
OUT_DIR = os.path.join(BASE, "data")

BLUE = "#2563eb"
ORANGE = "#f97316"

def main():
    if not os.path.exists(DB_PATH) or not os.path.exists(EXCEL_PATH):
        print("DB ya Excel file nahi mili! Pehle prepare_powerbi_dataset.py chalao.")
        sys.exit(1)

    # ── Source 1: SQLite (Web Dashboard) ──────────────────────
    conn = sqlite3.connect(DB_PATH)
    web_yearly = pd.read_sql_query(
        "SELECT year, SUM(cases_reported) as total_cases FROM crime_data GROUP BY year ORDER BY year", conn)
    web_state = pd.read_sql_query(
        "SELECT state, SUM(cases_reported) as total_cases FROM crime_data GROUP BY state ORDER BY total_cases DESC LIMIT 10", conn)
    web_crime = pd.read_sql_query(
        "SELECT crime_type, SUM(cases_reported) as total_cases FROM crime_data GROUP BY crime_type ORDER BY total_cases DESC", conn)
    web_cc = pd.read_sql_query(
        "SELECT crime_type, SUM(cases_reported) as reported, SUM(chargesheeted) as chargesheeted, SUM(convictions) as convictions FROM crime_data GROUP BY crime_type ORDER BY reported DESC", conn)
    conn.close()

    # ── Source 2: Power BI Excel ──────────────────────────────
    pbi_yearly = pd.read_excel(EXCEL_PATH, sheet_name="Yearly_Trends")
    pbi_state = pd.read_excel(EXCEL_PATH, sheet_name="State_Analytics").sort_values("total_cases", ascending=False).head(10)
    pbi_crime = pd.read_excel(EXCEL_PATH, sheet_name="Crime_Type_Analytics").sort_values("total_cases", ascending=False)

    COLORS = ["#4f46e5", "#0ea5e9", "#10b981", "#f59e0b", "#f43f5e",
              "#8b5cf6", "#06b6d4", "#84cc16", "#d946ef", "#14b8a6"]

    # ═══════════════════════════════════════════════════════════
    # CHART 1: Yearly Trend — Line Chart
    # ═══════════════════════════════════════════════════════════
    fig1 = make_subplots(rows=1, cols=2,
                         subplot_titles=["<b>WEB DASHBOARD</b> (SQLite DB)",
                                         "<b>POWER BI</b> (Excel Export)"],
                         horizontal_spacing=0.08)
    fig1.add_trace(go.Scatter(
        x=web_yearly["year"].astype(str), y=web_yearly["total_cases"],
        mode="lines+markers+text", name="Web",
        line=dict(color=BLUE, width=3, shape="spline"),
        marker=dict(size=10, color=BLUE),
        text=[f"{v:,}" for v in web_yearly["total_cases"]],
        textposition="top center", textfont=dict(size=9),
        showlegend=False
    ), row=1, col=1)
    fig1.add_trace(go.Scatter(
        x=pbi_yearly["year"].astype(str), y=pbi_yearly["total_cases"],
        mode="lines+markers+text", name="Power BI",
        line=dict(color=ORANGE, width=3, shape="spline"),
        marker=dict(size=10, color=ORANGE),
        text=[f"{v:,}" for v in pbi_yearly["total_cases"]],
        textposition="top center", textfont=dict(size=9),
        showlegend=False
    ), row=1, col=2)
    fig1.update_layout(
        title=dict(text="<b>YEARLY CRIME TREND</b>  —  Web vs Power BI", x=0.5, font=dict(size=16)),
        height=420, template="plotly_white",
        margin=dict(l=60, r=40, t=80, b=60)
    )
    fig1.update_yaxes(title_text="Cases Reported", tickformat=",", row=1, col=1)
    fig1.update_yaxes(title_text="Cases Reported", tickformat=",", row=1, col=2)
    path1 = os.path.join(OUT_DIR, "compare_yearly_trend.html")
    fig1.write_html(path1)
    print(f"[1/4] Yearly Trend saved: {path1}")

    # ═══════════════════════════════════════════════════════════
    # CHART 2: Top 10 States — Bar Chart
    # ═══════════════════════════════════════════════════════════
    fig2 = make_subplots(rows=1, cols=2,
                         subplot_titles=["<b>WEB DASHBOARD</b> (SQLite DB)",
                                         "<b>POWER BI</b> (Excel Export)"],
                         horizontal_spacing=0.08)
    fig2.add_trace(go.Bar(
        x=web_state["state"], y=web_state["total_cases"],
        marker=dict(color=BLUE), name="Web",
        text=[f"{v:,}" for v in web_state["total_cases"]],
        textposition="outside", textfont=dict(size=8),
        showlegend=False
    ), row=1, col=1)
    fig2.add_trace(go.Bar(
        x=pbi_state["state"], y=pbi_state["total_cases"],
        marker=dict(color=ORANGE), name="Power BI",
        text=[f"{v:,}" for v in pbi_state["total_cases"]],
        textposition="outside", textfont=dict(size=8),
        showlegend=False
    ), row=1, col=2)
    fig2.update_layout(
        title=dict(text="<b>TOP 10 STATES</b>  —  Web vs Power BI", x=0.5, font=dict(size=16)),
        height=450, template="plotly_white",
        margin=dict(l=60, r=40, t=80, b=100)
    )
    fig2.update_xaxes(tickangle=-35, tickfont=dict(size=9))
    fig2.update_yaxes(title_text="Cases Reported", tickformat=",", row=1, col=1)
    fig2.update_yaxes(tickformat=",", row=1, col=2)
    path2 = os.path.join(OUT_DIR, "compare_top_states.html")
    fig2.write_html(path2)
    print(f"[2/4] Top States saved: {path2}")

    # ═══════════════════════════════════════════════════════════
    # CHART 3: Crime Type Donut — Pie Chart
    # ═══════════════════════════════════════════════════════════
    fig3 = make_subplots(rows=1, cols=2,
                         specs=[[{"type": "pie"}, {"type": "pie"}]],
                         subplot_titles=["<b>WEB DASHBOARD</b> (SQLite DB)",
                                         "<b>POWER BI</b> (Excel Export)"])
    fig3.add_trace(go.Pie(
        labels=web_crime["crime_type"], values=web_crime["total_cases"],
        hole=0.45, marker=dict(colors=COLORS[:len(web_crime)]),
        textinfo="percent+label", textfont=dict(size=9),
        showlegend=False
    ), row=1, col=1)
    fig3.add_trace(go.Pie(
        labels=pbi_crime["crime_type"], values=pbi_crime["total_cases"],
        hole=0.45, marker=dict(colors=COLORS[:len(pbi_crime)]),
        textinfo="percent+label", textfont=dict(size=9),
        showlegend=False
    ), row=1, col=2)
    fig3.update_layout(
        title=dict(text="<b>CRIME TYPE DISTRIBUTION (DONUT)</b>  —  Web vs Power BI", x=0.5, font=dict(size=16)),
        height=450, template="plotly_white",
        margin=dict(l=30, r=30, t=80, b=30)
    )
    path3 = os.path.join(OUT_DIR, "compare_crime_type_donut.html")
    fig3.write_html(path3)
    print(f"[3/4] Crime Type Donut saved: {path3}")

    # ═══════════════════════════════════════════════════════════
    # CHART 4: Reported vs Chargesheeted vs Convictions
    # ═══════════════════════════════════════════════════════════
    fig4 = make_subplots(rows=1, cols=2,
                         subplot_titles=["<b>WEB DASHBOARD</b> (SQLite DB)",
                                         "<b>POWER BI</b> (Excel Export)"],
                         horizontal_spacing=0.08)
    for col_idx, (src_df, src_name) in enumerate([(web_cc, "Web"), (pbi_crime, "PBI")], 1):
        rep_col = "reported" if "reported" in src_df.columns else "total_cases"
        chg_col = "chargesheeted" if "chargesheeted" in src_df.columns else "total_chargesheeted"
        conv_col = "convictions" if "convictions" in src_df.columns else "total_convictions"
        fig4.add_trace(go.Bar(
            x=src_df["crime_type"], y=src_df[rep_col],
            name="Reported" if col_idx == 1 else "", marker=dict(color="#3b82f6"),
            showlegend=(col_idx == 1)
        ), row=1, col=col_idx)
        fig4.add_trace(go.Bar(
            x=src_df["crime_type"], y=src_df[chg_col],
            name="Chargesheeted" if col_idx == 1 else "", marker=dict(color="#f59e0b"),
            showlegend=(col_idx == 1)
        ), row=1, col=col_idx)
        fig4.add_trace(go.Bar(
            x=src_df["crime_type"], y=src_df[conv_col],
            name="Convictions" if col_idx == 1 else "", marker=dict(color="#10b981"),
            showlegend=(col_idx == 1)
        ), row=1, col=col_idx)
    fig4.update_layout(
        title=dict(text="<b>REPORTED vs CHARGESHEETED vs CONVICTIONS</b>  —  Web vs Power BI", x=0.5, font=dict(size=15)),
        barmode="group", height=470, template="plotly_white",
        margin=dict(l=60, r=40, t=80, b=100),
        legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center")
    )
    fig4.update_xaxes(tickangle=-30, tickfont=dict(size=9))
    fig4.update_yaxes(title_text="Count", tickformat=",", row=1, col=1)
    fig4.update_yaxes(tickformat=",", row=1, col=2)
    path4 = os.path.join(OUT_DIR, "compare_reported_vs_conviction.html")
    fig4.write_html(path4)
    print(f"[4/4] Reported vs Conviction saved: {path4}")

    print()
    print("=" * 60)
    print("  DONE! 4 comparison charts saved in data/ folder.")
    print("  Browser mein kholke dekh lo — left=Web, right=PowerBI")
    print("=" * 60)

if __name__ == "__main__":
    main()
