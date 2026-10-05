import os
from flask import Blueprint, render_template, request, send_file, current_app
from flask_login import login_required
from config import Config
from models.crime_model import CrimeModel
from services.visualization_service import VisualizationService

powerbi_bp = Blueprint('powerbi', __name__)

@powerbi_bp.route('/powerbi')
@login_required
def index():
    state = request.args.get('state', '').strip()
    district = request.args.get('district', '').strip()
    year = request.args.get('year', '').strip()
    crime_type = request.args.get('crime_type', '').strip()

    filters = {}
    if state and state.lower() != 'all': filters['state'] = state
    if district and district.lower() != 'all': filters['district'] = district
    if year and year.lower() != 'all': filters['year'] = year
    if crime_type and crime_type.lower() != 'all': filters['crime_type'] = crime_type

    # Summary statistics & interactive visualizations
    stats = CrimeModel.get_summary_stats(filters=filters)
    charts = VisualizationService.get_dashboard_charts(filters=filters)

    # Distinct dropdown options
    states = CrimeModel.get_distinct_states()
    years = CrimeModel.get_distinct_years()
    crime_types = CrimeModel.get_distinct_crime_types()

    # Calculate conviction rate percentage
    total_chargesheeted = stats.get('total_chargesheeted', 0)
    total_convictions = stats.get('total_convictions', 0)
    total_cases = stats.get('total_cases', 0)
    
    conviction_rate = 0.0
    if total_chargesheeted and total_chargesheeted > 0:
        conviction_rate = round((total_convictions / total_chargesheeted) * 100, 2)

    chargesheet_rate = 0.0
    if total_cases and total_cases > 0:
        chargesheet_rate = round((total_chargesheeted / total_cases) * 100, 2)

    # Top high-impact areas/districts for the Power BI Matrix table
    top_records = CrimeModel.get_top_crime_areas(limit=12, filters=filters)

    embed_url = Config.POWERBI_EMBED_URL

    return render_template(
        'powerbi.html',
        embed_url=embed_url,
        stats=stats,
        charts=charts,
        states=states,
        years=years,
        crime_types=crime_types,
        filters=filters,
        conviction_rate=conviction_rate,
        chargesheet_rate=chargesheet_rate,
        top_records=top_records
    )

@powerbi_bp.route('/powerbi/download-dataset')
@login_required
def download_dataset():
    excel_path = os.path.join(Config.BASE_DIR, "data", "powerbi_crime_dataset.xlsx")
    if os.path.exists(excel_path):
        return send_file(
            excel_path,
            as_attachment=True,
            download_name="crime_analytics_powerbi_dataset.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    # Fallback to CSV
    csv_path = Config.SAMPLE_CSV_PATH
    return send_file(
        csv_path,
        as_attachment=True,
        download_name="sample_crime_data.csv",
        mimetype="text/csv"
    )
