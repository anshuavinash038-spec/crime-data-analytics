import pandas as pd
import numpy as np
from models.crime_model import CrimeModel

class AnalyticsService:
    @classmethod
    def get_full_analysis(cls, filters=None):
        records = CrimeModel.get_all(filters=filters)
        if not records:
            return {
                "summary": {},
                "state_stats": [],
                "district_stats": [],
                "area_stats": [],
                "crime_type_stats": [],
                "insights": ["No crime data available matching the selected filters."]
            }

        df = pd.DataFrame(records)

        # Ensure numeric columns
        num_cols = ["cases_reported", "chargesheeted", "convictions", "population", "crime_rate_per_100k", "year"]
        for col in num_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # Core Metrics using Pandas/NumPy
        total_cases = int(np.sum(df["cases_reported"]))
        avg_cases = float(np.mean(df["cases_reported"]))
        max_cases = int(np.max(df["cases_reported"]))
        min_cases = int(np.min(df["cases_reported"]))
        avg_crime_rate = float(np.mean(df["crime_rate_per_100k"]))
        total_chargesheeted = int(np.sum(df["chargesheeted"]))
        total_convictions = int(np.sum(df["convictions"]))

        conviction_rate = round((total_convictions / total_chargesheeted * 100), 2) if total_chargesheeted > 0 else 0.0
        chargesheet_rate = round((total_chargesheeted / total_cases * 100), 2) if total_cases > 0 else 0.0

        summary = {
            "total_records": len(df),
            "total_cases": total_cases,
            "avg_cases": round(avg_cases, 2),
            "max_cases": max_cases,
            "min_cases": min_cases,
            "avg_crime_rate": round(avg_crime_rate, 2),
            "total_chargesheeted": total_chargesheeted,
            "total_convictions": total_convictions,
            "conviction_rate": conviction_rate,
            "chargesheet_rate": chargesheet_rate,
            "total_states": int(df["state"].nunique()),
            "total_districts": int(df["district"].nunique()),
            "total_areas": int(df["area"].nunique()),
            "total_crime_types": int(df["crime_type"].nunique())
        }

        # Area-wise Statistics
        area_grp = df.groupby(["area", "district", "state"]).agg({
            "cases_reported": "sum",
            "chargesheeted": "sum",
            "convictions": "sum",
            "crime_rate_per_100k": "mean",
            "population": "mean"
        }).reset_index().sort_values(by="cases_reported", ascending=False)

        area_grp["conviction_rate"] = np.where(
            area_grp["chargesheeted"] > 0,
            np.round((area_grp["convictions"] / area_grp["chargesheeted"]) * 100, 2),
            0.0
        )
        area_stats = area_grp.to_dict(orient="records")

        # State-wise Statistics
        state_grp = df.groupby("state").agg({
            "cases_reported": "sum",
            "chargesheeted": "sum",
            "convictions": "sum",
            "crime_rate_per_100k": "mean"
        }).reset_index().sort_values(by="cases_reported", ascending=False)
        state_stats = state_grp.to_dict(orient="records")

        # District-wise Statistics
        district_grp = df.groupby(["district", "state"]).agg({
            "cases_reported": "sum",
            "chargesheeted": "sum",
            "convictions": "sum",
            "crime_rate_per_100k": "mean"
        }).reset_index().sort_values(by="cases_reported", ascending=False)
        district_stats = district_grp.to_dict(orient="records")

        # Crime Type Statistics
        type_grp = df.groupby("crime_type").agg({
            "cases_reported": "sum",
            "chargesheeted": "sum",
            "convictions": "sum"
        }).reset_index().sort_values(by="cases_reported", ascending=False)
        type_stats = type_grp.to_dict(orient="records")

        # Dynamic Analytical Insights
        insights = cls.generate_insights(df, area_stats, state_stats, type_stats)

        return {
            "summary": summary,
            "state_stats": state_stats,
            "district_stats": district_stats,
            "area_stats": area_stats,
            "crime_type_stats": type_stats,
            "insights": insights
        }

    @classmethod
    def generate_insights(cls, df, area_stats, state_stats, type_stats):
        insights = []
        if not area_stats:
            return ["No data to generate insights."]

        top_area = area_stats[0]
        insights.append(f"Area '{top_area['area']}' ({top_area['district']}, {top_area['state']}) has the highest number of reported crime cases ({top_area['cases_reported']:,}).")

        top_crime_type = type_stats[0] if type_stats else None
        if top_crime_type:
            insights.append(f"'{top_crime_type['crime_type']}' is the most common crime type across selected records with {top_crime_type['cases_reported']:,} total cases.")

        highest_rate_area = max(area_stats, key=lambda x: x["crime_rate_per_100k"]) if area_stats else None
        if highest_rate_area:
            insights.append(f"Area '{highest_rate_area['area']}' records the highest average crime rate per 100k population ({highest_rate_area['crime_rate_per_100k']:.2f}).")

        # YoY Growth check
        if "year" in df.columns and df["year"].nunique() > 1:
            yearly = df.groupby("year")["cases_reported"].sum().reset_index().sort_values(by="year")
            years = yearly["year"].tolist()
            if len(years) >= 2:
                y1, y2 = years[-2], years[-1]
                c1 = yearly[yearly["year"] == y1]["cases_reported"].values[0]
                c2 = yearly[yearly["year"] == y2]["cases_reported"].values[0]
                if c1 > 0:
                    pct_change = round(((c2 - c1) / c1) * 100, 2)
                    direction = "increased" if pct_change >= 0 else "decreased"
                    insights.append(f"Crime cases {direction} by {abs(pct_change)}% between year {y1} and {y2}.")

        top_state = state_stats[0] if state_stats else None
        if top_state:
            insights.append(f"State '{top_state['state']}' contains the highest volume of reported cases ({top_state['cases_reported']:,}).")

        return insights

    @classmethod
    def compare_areas(cls, area_names):
        if not area_names or len(area_names) < 2:
            return None

        records = CrimeModel.get_all()
        df = pd.DataFrame(records)
        if df.empty:
            return None

        df_filtered = df[df["area"].isin(area_names)]
        if df_filtered.empty:
            return None

        area_comp = df_filtered.groupby("area").agg({
            "cases_reported": "sum",
            "chargesheeted": "sum",
            "convictions": "sum",
            "crime_rate_per_100k": "mean",
            "population": "first",
            "district": "first",
            "state": "first"
        }).reset_index()

        area_comp["conviction_rate"] = np.where(
            area_comp["chargesheeted"] > 0,
            np.round((area_comp["convictions"] / area_comp["chargesheeted"]) * 100, 2),
            0.0
        )

        return area_comp.to_dict(orient="records")
