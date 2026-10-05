from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from models.crime_model import CrimeModel
from services.analytics_service import AnalyticsService

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/analysis')
@login_required
def index():
    state = request.args.get('state', '').strip()
    district = request.args.get('district', '').strip()
    area = request.args.get('area', '').strip()
    year = request.args.get('year', '').strip()

    filters = {}
    if state and state.lower() != 'all': filters['state'] = state
    if district and district.lower() != 'all': filters['district'] = district
    if area and area.lower() != 'all': filters['area'] = area
    if year and year.lower() != 'all': filters['year'] = year

    data = AnalyticsService.get_full_analysis(filters=filters)

    states = CrimeModel.get_distinct_states()
    districts = CrimeModel.get_districts_by_state(state)
    areas = CrimeModel.get_areas_by_district(district=district, state=state)
    all_areas = [r['area'] for r in CrimeModel.get_top_crime_areas(limit=50)]

    return render_template(
        'analysis.html',
        analysis=data,
        filters=filters,
        states=states,
        districts=districts,
        areas=areas,
        all_areas=sorted(list(set(all_areas)))
    )

@analysis_bp.route('/analysis/compare-areas', methods=['POST'])
@login_required
def compare_areas():
    req_json = request.get_json() or {}
    area_names = req_json.get('areas', [])

    if not area_names or len(area_names) < 2:
        return jsonify({'error': 'Please select at least 2 areas for comparison.'}), 400

    results = AnalyticsService.compare_areas(area_names)
    if not results:
        return jsonify({'error': 'No matching data found for selected areas.'}), 404

    return jsonify({'success': True, 'comparison': results})
