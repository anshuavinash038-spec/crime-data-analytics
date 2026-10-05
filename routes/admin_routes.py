import sys
import io
import csv
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, abort
from flask_login import login_required, current_user
from models.user_model import User
from models.crime_model import CrimeModel
from models.location_model import LocationModel
from services.database_service import DatabaseService
from services.activity_service import ActivityService
from routes.decorators import admin_required
from services.visualization_service import VisualizationService

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
def check_admin_access():
    if request.endpoint == 'admin.login':
        return
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login', next=request.url))
    if not current_user.is_admin:
        abort(403)

@admin_bp.route('/')
@admin_required
def index():
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/login')
def login():
    # Unified login: redirect to main /login
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('auth.login'))

# =============================================================================
# Admin Dashboard
# =============================================================================
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    stats = CrimeModel.get_summary_stats()
    all_users = User.get_all_users()
    users_count = len(all_users)
    recent_users = all_users[:5]
    recent_records = CrimeModel.get_all(limit=5)
    recent_logs = ActivityService.get_recent_logs(limit=8)
    db_type = DatabaseService.get_db_type()
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    return render_template(
        'admin/dashboard.html',
        stats=stats,
        users_count=users_count,
        recent_users=recent_users,
        recent_records=recent_records,
        recent_logs=recent_logs,
        db_type=db_type,
        python_version=python_version
    )

# =============================================================================
# Manage Crime Data (/admin/data)
# =============================================================================
@admin_bp.route('/data')
@admin_required
def crime_data():
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

    records = CrimeModel.get_all(filters=filters, limit=300)
    states = CrimeModel.get_distinct_states()
    districts = CrimeModel.get_districts_by_state(state)
    areas = CrimeModel.get_areas_by_district(district=district, state=state)
    years = CrimeModel.get_distinct_years()
    crime_types = CrimeModel.get_distinct_crime_types()

    return render_template(
        'admin/data.html',
        records=records,
        filters=filters,
        states=states,
        districts=districts,
        areas=areas,
        years=years,
        crime_types=crime_types
    )

@admin_bp.route('/data/add', methods=['POST'])
@admin_required
def add_crime_data():
    state = request.form.get('state', '').strip()
    district = request.form.get('district', '').strip()
    area = request.form.get('area', '').strip()
    year = request.form.get('year', '').strip()
    crime_type = request.form.get('crime_type', '').strip()
    cases_reported = request.form.get('cases_reported', '0').strip()
    chargesheeted = request.form.get('chargesheeted', '0').strip()
    convictions = request.form.get('convictions', '0').strip()
    population = request.form.get('population', '100000').strip()

    if not state or not district or not area or not year or not crime_type:
        flash('State, District, Area, Year, and Crime Type are mandatory fields.', 'danger')
        return redirect(url_for('admin.crime_data'))

    try:
        new_id = CrimeModel.create(
            state=state, district=district, area=area, year=year,
            crime_type=crime_type, cases_reported=cases_reported,
            chargesheeted=chargesheeted, convictions=convictions, population=population
        )
        ActivityService.log(
            "Add Crime Record",
            f"Added crime record #{new_id}: {crime_type} in {area}, {district}, {state} ({year})"
        )
        flash(f'Crime record #{new_id} for Area "{area}" created successfully!', 'success')
    except Exception as e:
        flash(f'Error adding record: {e}', 'danger')

    return redirect(url_for('admin.crime_data'))

@admin_bp.route('/data/edit/<int:record_id>', methods=['POST'])
@admin_required
def edit_crime_data(record_id):
    state = request.form.get('state', '').strip()
    district = request.form.get('district', '').strip()
    area = request.form.get('area', '').strip()
    year = request.form.get('year', '').strip()
    crime_type = request.form.get('crime_type', '').strip()
    cases_reported = request.form.get('cases_reported', '0').strip()
    chargesheeted = request.form.get('chargesheeted', '0').strip()
    convictions = request.form.get('convictions', '0').strip()
    population = request.form.get('population', '100000').strip()

    if not state or not district or not area or not year or not crime_type:
        flash('State, District, Area, Year, and Crime Type are mandatory fields.', 'danger')
        return redirect(url_for('admin.crime_data'))

    try:
        CrimeModel.update(
            record_id=record_id, state=state, district=district, area=area,
            year=year, crime_type=crime_type, cases_reported=cases_reported,
            chargesheeted=chargesheeted, convictions=convictions, population=population
        )
        ActivityService.log(
            "Edit Crime Record",
            f"Updated crime record #{record_id}: {crime_type} in {area}, {district}, {state} ({year})"
        )
        flash(f'Crime record ID #{record_id} updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating record: {e}', 'danger')

    return redirect(url_for('admin.crime_data'))

@admin_bp.route('/data/delete/<int:record_id>', methods=['POST'])
@admin_required
def delete_crime_data(record_id):
    rec = CrimeModel.get_by_id(record_id)
    try:
        CrimeModel.delete(record_id)
        area_info = f" ({rec['area']}, {rec['district']})" if rec else ""
        ActivityService.log(
            "Delete Crime Record",
            f"Deleted crime record #{record_id}{area_info}"
        )
        flash(f'Crime record ID #{record_id} deleted successfully.', 'info')
    except Exception as e:
        flash(f'Error deleting record: {e}', 'danger')

    return redirect(url_for('admin.crime_data'))

@admin_bp.route('/data/import', methods=['POST'])
@admin_required
def import_csv():
    file = request.files.get('csv_file')
    if not file or not file.filename.endswith('.csv'):
        flash('Invalid file uploaded. Please select a valid .csv file.', 'danger')
        return redirect(url_for('admin.crime_data'))

    try:
        stream = io.StringIO(file.stream.read().decode("utf-8", errors="replace"), newline=None)
        csv_reader = csv.DictReader(stream)

        required_cols = {"State", "District", "Area", "Year", "Crime_Type", "Cases_Reported"}
        fieldnames = set(csv_reader.fieldnames or [])
        if not required_cols.issubset(fieldnames):
            missing = required_cols - fieldnames
            flash(f'CSV Missing required columns: {", ".join(missing)}', 'danger')
            return redirect(url_for('admin.crime_data'))

        total_rows = 0
        imported_rows = 0
        failed_rows = 0
        valid_batch = []

        for row_idx, row in enumerate(csv_reader, start=2):
            total_rows += 1
            st = str(row.get("State", "")).strip()
            dist = str(row.get("District", "")).strip()
            ar = str(row.get("Area", "")).strip()
            yr = str(row.get("Year", "")).strip()
            ct = str(row.get("Crime_Type", "")).strip()

            if not st or not dist or not ar or not yr or not ct:
                failed_rows += 1
                continue

            try:
                yr_val = int(yr)
                cases = int(row.get("Cases_Reported", 0))
                chg = int(row.get("Chargesheeted", 0))
                conv = int(row.get("Convictions", 0))
                pop = int(row.get("Population", 100000))

                if cases < 0 or chg < 0 or conv < 0 or pop <= 0:
                    failed_rows += 1
                    continue

                valid_batch.append({
                    "state": st, "district": dist, "area": ar, "year": yr_val,
                    "crime_type": ct, "cases_reported": cases, "chargesheeted": chg,
                    "convictions": conv, "population": pop
                })

                if len(valid_batch) >= 1000:
                    CrimeModel.create_batch(valid_batch)
                    imported_rows += len(valid_batch)
                    valid_batch = []
            except Exception:
                failed_rows += 1

        if valid_batch:
            CrimeModel.create_batch(valid_batch)
            imported_rows += len(valid_batch)

        ActivityService.log(
            "CSV Data Import",
            f"Imported CSV file '{file.filename}': {imported_rows} valid records imported, {failed_rows} failed."
        )
        flash(f'CSV Import Result: Total {total_rows} rows | {imported_rows} Successfully Imported | {failed_rows} Skipped/Invalid', 'success' if failed_rows == 0 else 'warning')
    except Exception as e:
        flash(f'CSV Processing error: {e}', 'danger')

    return redirect(url_for('admin.crime_data'))

@admin_bp.route('/data/export')
@admin_required
def export_csv():
    records = CrimeModel.get_all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "State", "District", "Area", "Year", "Crime_Type", 
        "Cases_Reported", "Chargesheeted", "Convictions", "Population", "Crime_Rate_per_100k"
    ])

    for r in records:
        writer.writerow([
            r["id"], r["state"], r["district"], r["area"], r["year"],
            r["crime_type"], r["cases_reported"], r["chargesheeted"],
            r["convictions"], r["population"], r["crime_rate_per_100k"]
        ])

    output.seek(0)
    ActivityService.log("CSV Data Export", f"Exported full dataset ({len(records)} records)")
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=crime_data_export.csv"}
    )

# =============================================================================
# Manage Locations Hierarchy (/admin/locations)
# =============================================================================
@admin_bp.route('/locations')
@admin_required
def locations():
    states = LocationModel.get_all_states()
    selected_state = request.args.get('state', '').strip()
    selected_district = request.args.get('district', '').strip()

    districts = LocationModel.get_all_districts(state_name=selected_state)
    areas = LocationModel.get_all_areas(state_name=selected_state, district_name=selected_district, limit=300)
    total_areas_count = LocationModel.count_areas(state_name=selected_state, district_name=selected_district)

    return render_template(
        'admin/locations.html',
        states=states,
        districts=districts,
        areas=areas,
        selected_state=selected_state,
        selected_district=selected_district,
        total_areas_count=total_areas_count
    )

@admin_bp.route('/locations/state/add', methods=['POST'])
@admin_required
def add_state():
    name = request.form.get('state_name', '').strip()
    code = request.form.get('state_code', '').strip().upper()
    if not name:
        flash('State name is required.', 'danger')
        return redirect(url_for('admin.locations'))
    try:
        LocationModel.add_state(name, code)
        ActivityService.log("Add State", f"Added new state '{name}' ({code})")
        flash(f'State "{name}" added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding state: {e}', 'danger')
    return redirect(url_for('admin.locations'))

@admin_bp.route('/locations/state/edit/<int:state_id>', methods=['POST'])
@admin_required
def edit_state(state_id):
    name = request.form.get('state_name', '').strip()
    code = request.form.get('state_code', '').strip().upper()
    if not name:
        flash('State name is required.', 'danger')
        return redirect(url_for('admin.locations'))
    try:
        LocationModel.update_state(state_id, name, code)
        ActivityService.log("Edit State", f"Updated state ID #{state_id} to '{name}' ({code})")
        flash(f'State updated to "{name}" successfully!', 'success')
    except Exception as e:
        flash(f'Error updating state: {e}', 'danger')
    return redirect(url_for('admin.locations'))

@admin_bp.route('/locations/state/toggle/<int:state_id>', methods=['POST'])
@admin_required
def toggle_state(state_id):
    try:
        new_status = LocationModel.toggle_state_active(state_id)
        status_label = "Activated" if new_status == 1 else "Deactivated"
        ActivityService.log("Toggle State Status", f"{status_label} state ID #{state_id}")
        flash(f'State ID #{state_id} {status_label}.', 'info')
    except Exception as e:
        flash(f'Error toggling state: {e}', 'danger')
    return redirect(url_for('admin.locations'))

@admin_bp.route('/locations/district/add', methods=['POST'])
@admin_required
def add_district():
    state_id = request.form.get('state_id')
    name = request.form.get('district_name', '').strip()
    historical = request.form.get('historical_name', '').strip()
    if not state_id or not name:
        flash('State and District name are required.', 'danger')
        return redirect(url_for('admin.locations'))
    try:
        LocationModel.add_district(int(state_id), name, historical)
        ActivityService.log("Add District", f"Added district '{name}' under state ID #{state_id}")
        flash(f'District "{name}" added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding district: {e}', 'danger')
    return redirect(url_for('admin.locations'))

@admin_bp.route('/locations/district/edit/<int:district_id>', methods=['POST'])
@admin_required
def edit_district(district_id):
    name = request.form.get('district_name', '').strip()
    historical = request.form.get('historical_name', '').strip()
    if not name:
        flash('District name is required.', 'danger')
        return redirect(url_for('admin.locations'))
    try:
        LocationModel.update_district(district_id, name, historical)
        ActivityService.log("Edit District", f"Updated district ID #{district_id} to '{name}'")
        flash(f'District updated to "{name}" successfully!', 'success')
    except Exception as e:
        flash(f'Error updating district: {e}', 'danger')
    return redirect(url_for('admin.locations'))

@admin_bp.route('/locations/district/toggle/<int:district_id>', methods=['POST'])
@admin_required
def toggle_district(district_id):
    try:
        new_status = LocationModel.toggle_district_active(district_id)
        status_label = "Activated" if new_status == 1 else "Deactivated"
        ActivityService.log("Toggle District Status", f"{status_label} district ID #{district_id}")
        flash(f'District ID #{district_id} {status_label}.', 'info')
    except Exception as e:
        flash(f'Error toggling district: {e}', 'danger')
    return redirect(url_for('admin.locations'))

@admin_bp.route('/locations/area/add', methods=['POST'])
@admin_required
def add_area():
    district_id = request.form.get('district_id')
    name = request.form.get('area_name', '').strip()
    area_type = request.form.get('area_type', '').strip()
    if not district_id or not name:
        flash('District and Area name are required.', 'danger')
        return redirect(url_for('admin.locations'))
    try:
        LocationModel.add_area(int(district_id), name, area_type)
        ActivityService.log("Add Area", f"Added area '{name}' under district ID #{district_id}")
        flash(f'Level-3 Area "{name}" created successfully!', 'success')
    except Exception as e:
        flash(f'Error adding area: {e}', 'danger')
    return redirect(url_for('admin.locations'))

@admin_bp.route('/locations/area/edit/<int:area_id>', methods=['POST'])
@admin_required
def edit_area(area_id):
    name = request.form.get('area_name', '').strip()
    area_type = request.form.get('area_type', '').strip()
    if not name:
        flash('Area name is required.', 'danger')
        return redirect(url_for('admin.locations'))
    try:
        LocationModel.update_area(area_id, name, area_type)
        ActivityService.log("Edit Area", f"Updated area ID #{area_id} to '{name}'")
        flash(f'Area updated to "{name}" successfully!', 'success')
    except Exception as e:
        flash(f'Error updating area: {e}', 'danger')
    return redirect(url_for('admin.locations'))

@admin_bp.route('/locations/area/toggle/<int:area_id>', methods=['POST'])
@admin_required
def toggle_area(area_id):
    try:
        new_status = LocationModel.toggle_area_active(area_id)
        status_label = "Activated" if new_status == 1 else "Deactivated"
        ActivityService.log("Toggle Area Status", f"{status_label} area ID #{area_id}")
        flash(f'Area ID #{area_id} {status_label}.', 'info')
    except Exception as e:
        flash(f'Error toggling area: {e}', 'danger')
    return redirect(url_for('admin.locations'))

# =============================================================================
# Manage Users (/admin/users)
# =============================================================================
@admin_bp.route('/users')
@admin_required
def users():
    search = request.args.get('q', '').strip()
    role = request.args.get('role', '').strip()
    status = request.args.get('status', '').strip()

    all_users = User.get_all_users(search=search, role=role, status=status)
    return render_template('admin/users.html', users=all_users, search=search, role=role, status=status)

@admin_bp.route('/users/toggle/<int:user_id>', methods=['POST'])
@admin_required
def toggle_user(user_id):
    if user_id == current_user.id:
        flash('Security protection: You cannot deactivate your own account.', 'warning')
        return redirect(url_for('admin.users'))

    target_user = User.get_by_id(user_id)
    if not target_user:
        flash('User account not found.', 'danger')
        return redirect(url_for('admin.users'))

    if target_user.is_admin and target_user.is_active and User.count_admins() <= 1:
        flash('Security protection: Cannot deactivate the only active administrator.', 'danger')
        return redirect(url_for('admin.users'))

    new_status = User.toggle_active(user_id)
    label = "activated" if new_status == 1 else "deactivated"
    ActivityService.log("Toggle User Status", f"{label.title()} user {target_user.name} ({target_user.email})")
    flash(f'User "{target_user.name}" has been {label}.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/role/<int:user_id>', methods=['POST'])
@admin_required
def change_user_role(user_id):
    new_role = request.form.get('role', 'USER').upper()
    if user_id == current_user.id:
        flash('Security protection: You cannot alter your own administrative role.', 'warning')
        return redirect(url_for('admin.users'))

    target_user = User.get_by_id(user_id)
    if not target_user:
        flash('User account not found.', 'danger')
        return redirect(url_for('admin.users'))

    if target_user.is_admin and new_role != 'ADMIN' and User.count_admins() <= 1:
        flash('Security protection: Cannot remove admin privileges from the sole remaining administrator.', 'danger')
        return redirect(url_for('admin.users'))

    User.update_role(user_id, new_role)
    ActivityService.log("Change User Role", f"Changed role of {target_user.name} ({target_user.email}) to {new_role}")
    flash(f'User "{target_user.name}" role updated to {new_role}.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('Security protection: You cannot delete your own account.', 'warning')
        return redirect(url_for('admin.users'))

    target_user = User.get_by_id(user_id)
    if not target_user:
        flash('User account not found.', 'danger')
        return redirect(url_for('admin.users'))

    if target_user.is_admin and User.count_admins() <= 1:
        flash('Security protection: Cannot delete the only remaining administrator account.', 'danger')
        return redirect(url_for('admin.users'))

    User.delete_user(user_id)
    ActivityService.log("Delete User Account", f"Deleted user {target_user.name} ({target_user.email})")
    flash(f'User "{target_user.name}" deleted successfully.', 'info')
    return redirect(url_for('admin.users'))

# =============================================================================
# Audit / Activity Logs (/admin/audit)
# =============================================================================
@admin_bp.route('/audit')
@admin_required
def audit():
    action_filter = request.args.get('action', '').strip()
    logs = ActivityService.get_all_logs(limit=200, action_filter=action_filter)
    return render_template('admin/audit.html', logs=logs, action_filter=action_filter)

# =============================================================================
# Analytics & Visualization (/admin/analytics)
# =============================================================================
@admin_bp.route('/analytics')
@admin_required
def analytics():
    state = request.args.get('state', '').strip()
    district = request.args.get('district', '').strip()
    area = request.args.get('area', '').strip()
    year = request.args.get('year', '').strip()

    filters = {}
    if state and state.lower() != 'all': filters['state'] = state
    if district and district.lower() != 'all': filters['district'] = district
    if area and area.lower() != 'all': filters['area'] = area
    if year and year.lower() != 'all': filters['year'] = year

    charts = VisualizationService.get_dashboard_charts(filters=filters)
    states = CrimeModel.get_distinct_states()
    districts = CrimeModel.get_districts_by_state(state)
    areas = CrimeModel.get_areas_by_district(district=district, state=state)
    years = CrimeModel.get_distinct_years()
    stats = CrimeModel.get_summary_stats(filters=filters)

    return render_template(
        'admin/analytics.html',
        charts=charts,
        filters=filters,
        states=states,
        districts=districts,
        areas=areas,
        years=years,
        stats=stats
    )
