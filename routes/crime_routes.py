import io
import csv
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, abort
from flask_login import login_required, current_user
from models.crime_model import CrimeModel
from routes.decorators import admin_required

crime_bp = Blueprint('crime', __name__)

@crime_bp.route('/crime-data')
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

    records = CrimeModel.get_all(filters=filters, limit=300)
    states = CrimeModel.get_distinct_states()
    districts = CrimeModel.get_districts_by_state(state)
    areas = CrimeModel.get_areas_by_district(district=district, state=state)
    years = CrimeModel.get_distinct_years()
    crime_types = CrimeModel.get_distinct_crime_types()

    return render_template(
        'crime_data.html',
        records=records,
        filters=filters,
        states=states,
        districts=districts,
        areas=areas,
        years=years,
        crime_types=crime_types
    )

@crime_bp.route('/crime-data/export')
@login_required
def export_csv():
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

    records = CrimeModel.get_all(filters=filters)
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
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=crime_data_export.csv"}
    )

# Mutating routes: STRICTLY restricted to Administrators via @admin_required
@crime_bp.route('/crime-data/add', methods=['POST'])
@login_required
@admin_required
def add():
    return redirect(url_for('admin.add_crime_data'), code=307)

@crime_bp.route('/crime-data/edit/<int:record_id>', methods=['POST'])
@login_required
@admin_required
def edit(record_id):
    return redirect(url_for('admin.edit_crime_data', record_id=record_id), code=307)

@crime_bp.route('/crime-data/delete/<int:record_id>', methods=['POST'])
@login_required
@admin_required
def delete(record_id):
    return redirect(url_for('admin.delete_crime_data', record_id=record_id), code=307)

@crime_bp.route('/crime-data/import', methods=['POST'])
@login_required
@admin_required
def import_csv():
    return redirect(url_for('admin.import_csv'), code=307)
