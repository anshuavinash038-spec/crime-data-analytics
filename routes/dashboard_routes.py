from flask import Blueprint, render_template, request
from flask_login import login_required
from models.crime_model import CrimeModel
from models.location_model import LocationModel
from services.analytics_service import AnalyticsService
from services.visualization_service import VisualizationService

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def home():
    stats = CrimeModel.get_summary_stats()
    geo_stats = LocationModel.get_master_geo_stats()
    return render_template('index.html', stats=stats, geo_stats=geo_stats)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    state = request.args.get('state', '').strip()
    district = request.args.get('district', '').strip()
    area = request.args.get('area', '').strip()
    year = request.args.get('year', '').strip()
    crime_type = request.args.get('crime_type', '').strip()

    filters = {}
    if state and state.lower() != 'all': filters['state'] = state
    if district and district.lower() != 'all': filters['district'] = district
    if area and area.lower() != 'all': filters['area'] = area
    if year and year.lower() != 'all': filters['year'] = year
    if crime_type and crime_type.lower() != 'all': filters['crime_type'] = crime_type

    # Statistics & Charts
    summary_stats = CrimeModel.get_summary_stats(filters=filters)
    geo_stats = LocationModel.get_master_geo_stats()
    top_areas = CrimeModel.get_top_crime_areas(limit=150, filters=filters)
    charts = VisualizationService.get_dashboard_charts(filters=filters)
    analysis = AnalyticsService.get_full_analysis(filters=filters)

    # Filter dropdown lists (Returns all options when no filter is selected)
    states = CrimeModel.get_distinct_states()
    districts = CrimeModel.get_districts_by_state(state)
    areas = CrimeModel.get_areas_by_district(district=district, state=state)
    years = CrimeModel.get_distinct_years()
    crime_types = CrimeModel.get_distinct_crime_types()

    return render_template(
        'dashboard.html',
        stats=summary_stats,
        geo_stats=geo_stats,
        top_areas=top_areas,
        charts=charts,
        insights=analysis.get('insights', []),
        filters=filters,
        states=states,
        districts=districts,
        areas=areas,
        years=years,
        crime_types=crime_types
    )
