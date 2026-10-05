from flask import Blueprint, render_template, request
from flask_login import login_required
from models.crime_model import CrimeModel

search_bp = Blueprint('search', __name__)

@search_bp.route('/search')
@login_required
def index():
    state = request.args.get('state', '').strip()
    district = request.args.get('district', '').strip()
    area = request.args.get('area', '').strip()
    crime_type = request.args.get('crime_type', '').strip()
    year = request.args.get('year', '').strip()
    min_cases = request.args.get('min_cases', '').strip()
    max_cases = request.args.get('max_cases', '').strip()
    min_rate = request.args.get('min_rate', '').strip()
    max_rate = request.args.get('max_rate', '').strip()

    filters = {}
    if state and state.lower() != 'all': filters['state'] = state
    if district and district.lower() != 'all': filters['district'] = district
    if area and area.lower() != 'all': filters['area'] = area
    if crime_type and crime_type.lower() != 'all': filters['crime_type'] = crime_type
    if year and year.lower() != 'all': filters['year'] = year
    if min_cases: filters['min_cases'] = min_cases
    if max_cases: filters['max_cases'] = max_cases
    if min_rate: filters['min_rate'] = min_rate
    if max_rate: filters['max_rate'] = max_rate

    results = CrimeModel.get_all(filters=filters) if filters else []
    summary = CrimeModel.get_summary_stats(filters=filters) if filters else None

    states = CrimeModel.get_distinct_states()
    districts = CrimeModel.get_districts_by_state(state)
    areas = CrimeModel.get_areas_by_district(district=district, state=state)
    years = CrimeModel.get_distinct_years()
    crime_types = CrimeModel.get_distinct_crime_types()

    return render_template(
        'search.html',
        results=results,
        summary=summary,
        filters=filters,
        states=states,
        districts=districts,
        areas=areas,
        years=years,
        crime_types=crime_types
    )
