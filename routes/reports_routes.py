import os
from datetime import datetime
from flask import Blueprint, render_template, request, send_from_directory, flash, redirect, url_for
from flask_login import login_required
from config import Config
from models.crime_model import CrimeModel
from services.analytics_service import AnalyticsService
from services.report_service import ReportService

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
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

    analysis = AnalyticsService.get_full_analysis(filters=filters)
    chart_filename = ReportService.generate_report_chart(filters=filters)

    states = CrimeModel.get_distinct_states()
    districts = CrimeModel.get_districts_by_state(state)
    areas = CrimeModel.get_areas_by_district(district=district, state=state)
    years = CrimeModel.get_distinct_years()

    return render_template(
        'reports.html',
        analysis=analysis,
        chart_filename=chart_filename,
        filters=filters,
        states=states,
        districts=districts,
        areas=areas,
        years=years,
        generated_at=datetime.now().strftime("%d %B %Y, %I:%M %p")
    )

@reports_bp.route('/reports/chart/<filename>')
@login_required
def get_chart_image(filename):
    return send_from_directory(Config.REPORTS_DIR, filename)

@reports_bp.route('/reports/download-pdf')
@login_required
def download_pdf():
    state = request.args.get('state', '').strip()
    district = request.args.get('district', '').strip()
    area = request.args.get('area', '').strip()
    year = request.args.get('year', '').strip()

    filters = {}
    if state: filters['state'] = state
    if district: filters['district'] = district
    if area: filters['area'] = area
    if year: filters['year'] = year

    pdf_filename = ReportService.generate_pdf_report(filters=filters)
    return send_from_directory(
        Config.REPORTS_DIR,
        pdf_filename,
        as_attachment=True,
        download_name="National_Crime_Analytics_Report.pdf"
    )

