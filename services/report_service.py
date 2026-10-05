import os
import uuid
import pandas as pd
import matplotlib
matplotlib.use('Agg') # Non-interactive background backend
import matplotlib.pyplot as plt
from config import Config
from models.crime_model import CrimeModel

class ReportService:
    @classmethod
    def generate_report_chart(cls, filters=None):
        filters = filters or {}
        records = CrimeModel.get_all(filters=filters)
        if not records:
            return None

        df = pd.DataFrame(records)
        df["cases_reported"] = pd.to_numeric(df["cases_reported"], errors="coerce").fillna(0)

        # Matplotlib figure setup
        plt.figure(figsize=(10, 5), dpi=120)
        plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

        # Area or Crime Type Summary
        if filters.get("area"):
            grouped = df.groupby("crime_type")["cases_reported"].sum().sort_values(ascending=False)
            plt.title(f"Crime Cases Breakdown for Area: '{filters['area']}'", fontsize=14, fontweight='bold', pad=15)
            plt.xlabel("Crime Type")
        else:
            grouped = df.groupby("area")["cases_reported"].sum().sort_values(ascending=False).head(10)
            plt.title("Top Crime Affected Areas", fontsize=14, fontweight='bold', pad=15)
            plt.xlabel("Area")

        bars = plt.bar(grouped.index, grouped.values, color='#0056b3', edgecolor='black', alpha=0.85)

        # Add data values on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                     f'{int(height)}', ha='center', va='bottom', fontsize=9, fontweight='bold')

        plt.ylabel("Reported Cases")
        plt.xticks(rotation=30, ha='right')
        plt.tight_layout()

        # Save to PNG file
        os.makedirs(Config.REPORTS_DIR, exist_ok=True)
        
        # Cleanup old report files, keep latest 10
        try:
            existing = [os.path.join(Config.REPORTS_DIR, f) for f in os.listdir(Config.REPORTS_DIR) if f.startswith("report_") and f.endswith(".png")]
            if len(existing) > 10:
                existing.sort(key=os.path.getmtime)
                for old_f in existing[:-10]:
                    try:
                        os.remove(old_f)
                    except OSError:
                        pass
        except Exception:
            pass

        filename = f"report_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(Config.REPORTS_DIR, filename)
        plt.savefig(filepath)
        plt.close()

        return filename

    @classmethod
    def generate_pdf_report(cls, filters=None):
        from datetime import datetime
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from services.analytics_service import AnalyticsService

        filters = filters or {}
        analysis = AnalyticsService.get_full_analysis(filters=filters)
        summary = analysis.get("summary", {})

        os.makedirs(Config.REPORTS_DIR, exist_ok=True)
        pdf_filename = f"crime_report_{uuid.uuid4().hex[:8]}.pdf"
        pdf_path = os.path.join(Config.REPORTS_DIR, pdf_filename)

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=14
        )
        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            textColor=colors.HexColor('#1e293b'),
            spaceBefore=10,
            spaceAfter=6
        )

        elements = []

        # Header Title
        elements.append(Paragraph("Crime Data Analytics & Spatial Visualization System", title_style))
        elements.append(Paragraph(f"Official Analytical Brief • Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}", subtitle_style))
        elements.append(Spacer(1, 8))

        # Scope Table
        scope_data = [
            ["State Filter:", filters.get("state") or "All 28 States", "District Filter:", filters.get("district") or "All Districts"],
            ["Area Filter:", filters.get("area") or "All Areas", "Year Scope:", filters.get("year") or "All Multi-Year Records"]
        ]
        scope_table = Table(scope_data, colWidths=[100, 170, 100, 170])
        scope_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1e293b')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(scope_table)
        elements.append(Spacer(1, 14))

        # Key Metrics Table
        elements.append(Paragraph("1. Executive Incident & Disposal Statistics", heading_style))
        total_cases = summary.get("total_cases", 0)
        total_chargesheeted = summary.get("total_chargesheeted", 0)
        total_convictions = summary.get("total_convictions", 0)
        conviction_rate = summary.get("conviction_rate", 0.0)
        avg_rate = summary.get("avg_crime_rate", 0.0)

        metrics_data = [
            ["Total Cases Reported", "Chargesheeted Cases", "Total Convictions", "Conviction Rate", "Avg Rate / 100k"],
            [f"{total_cases:,}", f"{total_chargesheeted:,}", f"{total_convictions:,}", f"{conviction_rate}%", f"{avg_rate:.2f}"]
        ]
        metrics_table = Table(metrics_data, colWidths=[108, 108, 108, 108, 108])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, 1), 11),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 1), (-1, 1), colors.HexColor('#0f172a')),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f1f5f9')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#94a3b8')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(metrics_table)
        elements.append(Spacer(1, 14))

        # Chart Image
        chart_filename = cls.generate_report_chart(filters=filters)
        if chart_filename:
            chart_img_path = os.path.join(Config.REPORTS_DIR, chart_filename)
            if os.path.exists(chart_img_path):
                elements.append(Paragraph("2. Graphical Distribution Overview", heading_style))
                elements.append(RLImage(chart_img_path, width=540, height=270))
                elements.append(Spacer(1, 14))

        # Build Document
        doc.build(elements)
        return pdf_filename

