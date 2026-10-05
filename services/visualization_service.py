import json
import pandas as pd
import plotly
import plotly.graph_objects as go
from models.crime_model import CrimeModel

# Modern harmonious color palette
MODERN_PALETTE = [
    "#4f46e5", "#0ea5e9", "#10b981", "#f59e0b", "#f43f5e",
    "#8b5cf6", "#06b6d4", "#84cc16", "#d946ef", "#14b8a6",
    "#f97316", "#64748b"
]

class VisualizationService:

    @classmethod
    def _base_layout(cls, height=390, title_text=""):
        return dict(
            title=dict(
                text=title_text,
                font=dict(size=14, color="#0f172a", family="Segoe UI, -apple-system, sans-serif"),
                x=0.03, y=0.95
            ),
            template="plotly_white",
            margin=dict(l=60, r=40, t=65, b=65),
            height=height,
            font=dict(family="Segoe UI, -apple-system, sans-serif", size=11, color="#334155"),
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            hoverlabel=dict(
                bgcolor="#0f172a",
                font_size=12,
                font_color="#ffffff",
                font_family="Segoe UI, sans-serif",
                bordercolor="#334155"
            )
        )

    @classmethod
    def get_empty_chart(cls, title="No Data", message="No records found for selected filters."):
        fig = go.Figure()
        fig.add_annotation(
            text=f"<b>{message}</b><br><span style='font-size:12px;color:#94a3b8;'>Try adjusting or resetting your filters</span>",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=13, color="#64748b")
        )
        layout = cls._base_layout(height=340, title_text=title)
        layout.update(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        fig.update_layout(**layout)
        return json.dumps(fig.to_dict())

    @classmethod
    def get_dashboard_charts(cls, filters=None):
        try:
            records = CrimeModel.get_all(filters=filters, limit=100000)
        except Exception:
            records = []

        if not records:
            empty = cls.get_empty_chart()
            return {k: empty for k in [
                "chart_year", "chart_state", "chart_district", "chart_area",
                "chart_crime_type", "chart_chargesheet_conviction",
                "chart_top_areas", "chart_heatmap"
            ]}

        df = pd.DataFrame(records)
        for col in ["cases_reported", "chargesheeted", "convictions", "crime_rate_per_100k"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        
        # Ensure year is integer string for clean categorical axis
        df["year"] = pd.to_numeric(df["year"], errors="coerce").fillna(0).astype(int).astype(str)

        f = filters or {}
        s = (f.get("state") or "").strip()
        d = (f.get("district") or "").strip()
        if s.lower() == "all": s = ""
        if d.lower() == "all": d = ""
        scope = f"{s} › {d}" if s and d else (s or d or "All 28 States")

        # ── 1. Yearly Crime Trend (Smooth Spline + Gradient Area Fill) ────
        try:
            yearly = (df.groupby("year")["cases_reported"]
                      .sum().reset_index()
                      .sort_values("year"))
            years_list = [str(y) for y in yearly["year"].tolist()]
            cases_list = [int(c) for c in yearly["cases_reported"].tolist()]

            fig1 = go.Figure()
            # Gradient area under curve
            fig1.add_trace(go.Scatter(
                x=years_list,
                y=cases_list,
                mode="lines+markers+text",
                name="Annual Cases",
                line=dict(color="#2563eb", width=3.5, shape="spline", smoothing=1.1),
                marker=dict(size=11, color="#1d4ed8", line=dict(width=2.5, color="#ffffff")),
                fill="tozeroy",
                fillcolor="rgba(37, 99, 235, 0.08)",
                text=[f"{c:,}" for c in cases_list],
                textposition="top center",
                textfont=dict(size=10, color="#1e293b", family="Segoe UI, sans-serif"),
                hovertemplate="<b>Year %{x}</b><br>Total Cases Reported: <b>%{y:,}</b><extra></extra>"
            ))

            layout1 = cls._base_layout(height=370, title_text=f"📈 Yearly Crime Trend — {scope}")
            layout1.update(
                xaxis=dict(
                    title="Calendar Year",
                    type="category",
                    gridcolor="#f1f5f9",
                    linecolor="#cbd5e1",
                    tickfont=dict(size=11, color="#475569")
                ),
                yaxis=dict(
                    title="Cases Reported",
                    tickformat=",",
                    gridcolor="#f1f5f9",
                    linecolor="#cbd5e1",
                    tickfont=dict(size=11, color="#475569"),
                    zeroline=False
                )
            )
            fig1.update_layout(**layout1)
            chart_year = json.dumps(fig1.to_dict())
        except Exception as e:
            chart_year = cls.get_empty_chart("Yearly Trend", str(e))

        # ── 2. Crime Type Distribution (Donut with Centerpiece Metric) ───
        try:
            type_df = (df.groupby("crime_type")["cases_reported"]
                       .sum().reset_index()
                       .sort_values("cases_reported", ascending=False))
            types_list = [str(t) for t in type_df["crime_type"].tolist()]
            values_list = [int(v) for v in type_df["cases_reported"].tolist()]
            total_cases_all = sum(values_list)

            # Formatted total for centerpiece (e.g. 11.3M)
            if total_cases_all >= 1_000_000:
                center_text = f"<b>{total_cases_all / 1_000_000:.1f}M</b><br><span style='font-size:10px;color:#64748b'>Total Cases</span>"
            else:
                center_text = f"<b>{total_cases_all:,}</b><br><span style='font-size:10px;color:#64748b'>Total Cases</span>"

            fig2 = go.Figure()
            fig2.add_trace(go.Pie(
                labels=types_list,
                values=values_list,
                hole=0.48,
                marker=dict(colors=MODERN_PALETTE[:len(types_list)], line=dict(color="#ffffff", width=2)),
                textposition="outside",
                textinfo="percent+label",
                textfont=dict(size=10, family="Segoe UI, sans-serif"),
                hovertemplate="<b>%{label}</b><br>Reported: <b>%{value:,}</b><br>Share: <b>%{percent}</b><extra></extra>",
                pull=[0.02] * len(types_list)
            ))

            layout2 = cls._base_layout(height=400, title_text=f"🍩 Crime Type Distribution — {scope}")
            layout2.update(
                margin=dict(l=20, r=130, t=65, b=25),
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle", y=0.5,
                    xanchor="left", x=1.02,
                    font=dict(size=10, color="#334155")
                ),
                annotations=[
                    dict(
                        text=center_text,
                        x=0.5, y=0.5,
                        font_size=15,
                        font_color="#0f172a",
                        font_family="Segoe UI, sans-serif",
                        showarrow=False
                    )
                ]
            )
            fig2.update_layout(**layout2)
            chart_crime_type = json.dumps(fig2.to_dict())
        except Exception as e:
            chart_crime_type = cls.get_empty_chart("Crime Type Distribution", str(e))

        # ── 3. Crime by State (Gradient Top States Bar) ───────────────────
        try:
            state_df = (df.groupby("state")["cases_reported"]
                        .sum().reset_index()
                        .sort_values("cases_reported", ascending=False)
                        .head(20))
            states_list = [str(st) for st in state_df["state"].tolist()]
            state_cases = [int(c) for c in state_df["cases_reported"].tolist()]

            fig3 = go.Figure()
            fig3.add_trace(go.Bar(
                x=states_list,
                y=state_cases,
                marker=dict(
                    color=state_cases,
                    colorscale=[
                        [0.0, "#93c5fd"],
                        [0.5, "#3b82f6"],
                        [1.0, "#1d4ed8"]
                    ],
                    showscale=False,
                    line=dict(color="#1e40af", width=1)
                ),
                text=[f"{c:,}" for c in state_cases],
                textposition="outside",
                textfont=dict(size=9, color="#1e293b"),
                hovertemplate="<b>%{x}</b><br>Total Cases: <b>%{y:,}</b><extra></extra>"
            ))

            layout3 = cls._base_layout(height=380, title_text=f"🗺️ State-wise Crime Comparison — {scope}")
            layout3.update(
                xaxis=dict(title="", tickangle=-35, tickfont=dict(size=10, color="#475569"), gridcolor="#f1f5f9"),
                yaxis=dict(title="Cases Reported", tickformat=",", gridcolor="#f1f5f9", zeroline=False)
            )
            fig3.update_layout(**layout3)
            chart_state = json.dumps(fig3.to_dict())
        except Exception as e:
            chart_state = cls.get_empty_chart("State Comparison", str(e))

        # ── 4. Top 15 Districts (Horizontal Bar) ─────────────────────────
        try:
            dist_df = (df.groupby("district")["cases_reported"]
                       .sum().reset_index()
                       .sort_values("cases_reported", ascending=True)
                       .tail(15))
            dist_names = [str(dt) for dt in dist_df["district"].tolist()]
            dist_cases = [int(c) for c in dist_df["cases_reported"].tolist()]

            fig4 = go.Figure()
            fig4.add_trace(go.Bar(
                y=dist_names,
                x=dist_cases,
                orientation="h",
                marker=dict(
                    color=dist_cases,
                    colorscale=[
                        [0.0, "#fed7aa"],
                        [0.5, "#f97316"],
                        [1.0, "#c2410c"]
                    ],
                    showscale=False,
                    line=dict(color="#ea580c", width=1)
                ),
                text=[f"{c:,}" for c in dist_cases],
                textposition="outside",
                textfont=dict(size=9, color="#1e293b"),
                hovertemplate="<b>District: %{y}</b><br>Reported Cases: <b>%{x:,}</b><extra></extra>"
            ))

            layout4 = cls._base_layout(height=420, title_text=f"🏙️ Top 15 Districts — {scope}")
            layout4.update(
                margin=dict(l=150, r=50, t=65, b=45),
                xaxis=dict(title="Cases Reported", tickformat=",", gridcolor="#f1f5f9", zeroline=False),
                yaxis=dict(title="", automargin=True, tickfont=dict(size=10, color="#334155"))
            )
            fig4.update_layout(**layout4)
            chart_district = json.dumps(fig4.to_dict())
        except Exception as e:
            chart_district = cls.get_empty_chart("Top Districts", str(e))

        # ── 5. Top 15 Sub-Districts / Tehsils (Horizontal Bar) ────────────
        try:
            area_df = (df.groupby("area")["cases_reported"]
                       .sum().reset_index()
                       .sort_values("cases_reported", ascending=True)
                       .tail(15))
            area_names = [str(a) for a in area_df["area"].tolist()]
            area_cases = [int(c) for c in area_df["cases_reported"].tolist()]

            fig5 = go.Figure()
            fig5.add_trace(go.Bar(
                y=area_names,
                x=area_cases,
                orientation="h",
                marker=dict(
                    color=area_cases,
                    colorscale=[
                        [0.0, "#e9d5ff"],
                        [0.5, "#a855f7"],
                        [1.0, "#6b21a8"]
                    ],
                    showscale=False,
                    line=dict(color="#7e22ce", width=1)
                ),
                text=[f"{c:,}" for c in area_cases],
                textposition="outside",
                textfont=dict(size=9, color="#1e293b"),
                hovertemplate="<b>Sub-District / Tehsil: %{y}</b><br>Reported Cases: <b>%{x:,}</b><extra></extra>"
            ))

            layout5 = cls._base_layout(height=420, title_text=f"📍 Top 15 Sub-Districts / Tehsils — {scope}")
            layout5.update(
                margin=dict(l=160, r=50, t=65, b=45),
                xaxis=dict(title="Cases Reported", tickformat=",", gridcolor="#f1f5f9", zeroline=False),
                yaxis=dict(title="", automargin=True, tickfont=dict(size=10, color="#334155"))
            )
            fig5.update_layout(**layout5)
            chart_top_areas = json.dumps(fig5.to_dict())
        except Exception as e:
            chart_top_areas = cls.get_empty_chart("Top Areas", str(e))

        # ── 6. Reported vs Chargesheeted vs Convictions (Grouped Bar) ───
        try:
            cc_df = (df.groupby("crime_type")[
                ["cases_reported", "chargesheeted", "convictions"]
            ].sum().reset_index()
             .sort_values("cases_reported", ascending=False))
            
            c_types = [str(ct) for ct in cc_df["crime_type"].tolist()]
            c_rep = [int(r) for r in cc_df["cases_reported"].tolist()]
            c_chg = [int(ch) for ch in cc_df["chargesheeted"].tolist()]
            c_cnv = [int(cn) for cn in cc_df["convictions"].tolist()]

            fig6 = go.Figure()
            fig6.add_trace(go.Bar(
                x=c_types, y=c_rep,
                name="Reported Incidents",
                marker=dict(color="#3b82f6", line=dict(color="#1d4ed8", width=1)),
                hovertemplate="<b>%{x}</b><br>Reported: <b>%{y:,}</b><extra></extra>"
            ))
            fig6.add_trace(go.Bar(
                x=c_types, y=c_chg,
                name="Chargesheeted (Police)",
                marker=dict(color="#f59e0b", line=dict(color="#d97706", width=1)),
                hovertemplate="<b>%{x}</b><br>Chargesheeted: <b>%{y:,}</b><extra></extra>"
            ))
            fig6.add_trace(go.Bar(
                x=c_types, y=c_cnv,
                name="Convictions (Judiciary)",
                marker=dict(color="#10b981", line=dict(color="#059669", width=1)),
                hovertemplate="<b>%{x}</b><br>Convictions: <b>%{y:,}</b><extra></extra>"
            ))

            layout6 = cls._base_layout(height=420, title_text=f"⚖️ Reported vs Chargesheeted vs Convictions — {scope}")
            layout6.update(
                barmode="group",
                legend=dict(
                    orientation="h",
                    yanchor="bottom", y=-0.35,
                    xanchor="center", x=0.5,
                    font=dict(size=11, color="#334155")
                ),
                xaxis=dict(title="", tickangle=-30, tickfont=dict(size=10, color="#475569"), gridcolor="#f1f5f9"),
                yaxis=dict(title="Case Count", tickformat=",", gridcolor="#f1f5f9", zeroline=False)
            )
            fig6.update_layout(**layout6)
            chart_cc = json.dumps(fig6.to_dict())
        except Exception as e:
            chart_cc = cls.get_empty_chart("Chargesheet vs Convictions", str(e))

        # ── 7. Heatmap — Sub-Districts × Crime Types (2D Matrix) ─────────
        try:
            top40 = (df.groupby("area")["cases_reported"]
                     .sum().nlargest(40).index.tolist())
            hm_df = df[df["area"].isin(top40)]
            pivot = (hm_df.pivot_table(
                index="area", columns="crime_type",
                values="cases_reported", aggfunc="sum"
            ).fillna(0))
            pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]

            areas_list = [str(a) for a in pivot.index.tolist()]
            crimes_list = [str(c) for c in pivot.columns.tolist()]
            z_values = [[int(val) for val in pivot.loc[area].tolist()] for area in areas_list]

            n = len(areas_list)
            hm_height = max(500, min(1600, n * 26 + 150))

            fig7 = go.Figure(data=go.Heatmap(
                z=z_values,
                x=crimes_list,
                y=areas_list,
                colorscale="YlOrRd",
                colorbar=dict(
                    title=dict(text="Cases", side="top", font=dict(size=11)),
                    thickness=14,
                    len=0.7,
                    tickfont=dict(size=10)
                ),
                hovertemplate=(
                    "<b>Sub-District / Tehsil:</b> %{y}<br>"
                    "<b>Crime Category:</b> %{x}<br>"
                    "<b>Reported Incidents:</b> <b>%{z:,}</b>"
                    "<extra></extra>"
                )
            ))
            layout7 = cls._base_layout(
                height=hm_height,
                title_text=f"🔥 Sub-District × Crime Type Heatmap — {scope} (Top {n} Sub-Districts)"
            )
            layout7.update(
                margin=dict(l=190, r=80, t=80, b=130),
                xaxis=dict(title="Crime Classification", side="bottom", tickangle=-35, tickfont=dict(size=11, color="#334155")),
                yaxis=dict(title="Sub-District / Tehsil", tickfont=dict(size=10, color="#334155"), automargin=True)
            )
            fig7.update_layout(**layout7)
            chart_heatmap = json.dumps(fig7.to_dict())
        except Exception as e:
            chart_heatmap = cls.get_empty_chart("Heatmap Matrix", str(e))

        return {
            "chart_year":                   chart_year,
            "chart_state":                  chart_state,
            "chart_district":               chart_district,
            "chart_area":                   chart_top_areas,
            "chart_crime_type":             chart_crime_type,
            "chart_chargesheet_conviction": chart_cc,
            "chart_top_areas":              chart_top_areas,
            "chart_heatmap":                chart_heatmap,
        }
