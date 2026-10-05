from flask import Blueprint, render_template, request
from flask_login import login_required
from models.crime_model import CrimeModel
from services.visualization_service import VisualizationService

visualization_bp = Blueprint('visualization', __name__)

@visualization_bp.route('/visualization')
@login_required
def index():
    state = request.args.get('state', '').strip()
    district = request.args.get('district', '').strip()
    area = request.args.get('area', '').strip()
    year = request.args.get('year', '').strip()

    filters = {}
    if state: filters['state'] = state
    if district: filters['district'] = district
    if area: filters['area'] = area
    if year: filters['year'] = year

    charts = VisualizationService.get_dashboard_charts(filters=filters)

    states = CrimeModel.get_distinct_states()
    districts = CrimeModel.get_districts_by_state(state)
    areas = CrimeModel.get_areas_by_district(district=district, state=state)
    years = CrimeModel.get_distinct_years()

    return render_template(
        'visualization.html',
        charts=charts,
        filters=filters,
        states=states,
        districts=districts,
        areas=areas,
        years=years
    )
