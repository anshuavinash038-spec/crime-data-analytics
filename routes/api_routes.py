from flask import Blueprint, jsonify, request
from flask_login import login_required
from models.crime_model import CrimeModel
from services.analytics_service import AnalyticsService
from services.visualization_service import VisualizationService

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/summary')
@login_required
def summary():
    stats = CrimeModel.get_summary_stats()
    return jsonify(stats)

@api_bp.route('/trends')
@login_required
def trends():
    records = CrimeModel.get_all()
    if not records:
        return jsonify([])
    import pandas as pd
    df = pd.DataFrame(records)
    yearly = df.groupby("year")["cases_reported"].sum().reset_index().sort_values("year")
    return jsonify(yearly.to_dict(orient="records"))

@api_bp.route('/state-statistics')
@login_required
def state_statistics():
    analysis = AnalyticsService.get_full_analysis()
    return jsonify(analysis.get("state_stats", []))

@api_bp.route('/district-statistics')
@login_required
def district_statistics():
    analysis = AnalyticsService.get_full_analysis()
    return jsonify(analysis.get("district_stats", []))

@api_bp.route('/area-statistics')
@login_required
def area_statistics():
    analysis = AnalyticsService.get_full_analysis()
    return jsonify(analysis.get("area_stats", []))

@api_bp.route('/crime-types')
@login_required
def crime_types():
    types = CrimeModel.get_distinct_crime_types()
    return jsonify(types)

@api_bp.route('/filters')
@login_required
def filters():
    states = CrimeModel.get_distinct_states()
    years = CrimeModel.get_distinct_years()
    c_types = CrimeModel.get_distinct_crime_types()
    return jsonify({
        "states": states,
        "years": years,
        "crime_types": c_types
    })

@api_bp.route('/search')
@login_required
def search():
    filters_dict = {
        "state": request.args.get("state"),
        "district": request.args.get("district"),
        "area": request.args.get("area"),
        "year": request.args.get("year"),
        "crime_type": request.args.get("crime_type")
    }
    filters_dict = {k: v for k, v in filters_dict.items() if v}
    records = CrimeModel.get_all(filters=filters_dict)
    return jsonify(records)

@api_bp.route('/dashboard-data')
@login_required
def dashboard_data():
    filters_dict = {
        "state": request.args.get("state"),
        "district": request.args.get("district"),
        "area": request.args.get("area"),
        "year": request.args.get("year")
    }
    filters_dict = {k: v for k, v in filters_dict.items() if v}
    stats = CrimeModel.get_summary_stats(filters=filters_dict)
    charts = VisualizationService.get_dashboard_charts(filters=filters_dict)
    return jsonify({"stats": stats, "charts": charts})

# =======================================================
# Dynamic Cascading Dropdown APIs
# =======================================================

@api_bp.route('/states')
def get_states():
    """Returns all available normalized states from master tables."""
    states_list = CrimeModel.get_distinct_states()
    return jsonify(states_list)

@api_bp.route('/districts')
def get_districts_query():
    """
    Returns districts for a state via query param ?state=...
    If state is 'all' or omitted, returns all districts.
    """
    state = request.args.get('state', '').strip()
    districts_list = CrimeModel.get_districts_by_state(state)
    return jsonify(districts_list)

@api_bp.route('/districts/<path:state>')
def get_districts_path(state):
    """Path-based route for backward compatibility."""
    districts_list = CrimeModel.get_districts_by_state(state)
    return jsonify(districts_list)

@api_bp.route('/areas')
def get_areas_query():
    """
    Returns areas filtered by state and/or district via query params:
    ?state=...&district=...
    - If both state & district provided: returns areas for that state + district
    - If only district provided: returns areas for that district
    - If only state provided: returns all areas for that state
    - If neither or both 'all': returns all areas
    """
    state = request.args.get('state', '').strip()
    district = request.args.get('district', '').strip()
    areas_list = CrimeModel.get_areas_by_district(district=district, state=state)
    return jsonify(areas_list)

@api_bp.route('/areas/<path:district>')
def get_areas_path(district):
    """Path-based route for backward compatibility."""
    state = request.args.get('state', '').strip()
    areas_list = CrimeModel.get_areas_by_district(district=district, state=state)
    return jsonify(areas_list)

@api_bp.route('/areas-by-state/<path:state>')
def get_areas_by_state_path(state):
    """Return all areas belonging to a given state."""
    areas_list = CrimeModel.get_areas_by_state(state)
    return jsonify(areas_list)

@api_bp.route('/locations/districts/<int:state_id>')
def get_locations_districts_by_id(state_id):
    from models.location_model import LocationModel
    districts = LocationModel.get_districts_by_state_id(state_id)
    return jsonify(districts)

@api_bp.route('/locations/areas/<int:district_id>')
def get_locations_areas_by_id(district_id):
    from models.location_model import LocationModel
    areas = LocationModel.get_areas_by_district_id(district_id)
    return jsonify(areas)

