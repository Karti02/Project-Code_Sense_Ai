

import os
from datetime import datetime

from flask import Blueprint, render_template, send_from_directory, current_app
from flask_login import login_required, current_user

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet

from app.services import stats_service

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


def _build_pdf(user, period_label, summary_rows, extra_rows, file_path):
    doc = SimpleDocTemplate(file_path, pagesize=A4,
                             topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("CodeSense AI - Productivity Report", styles["Title"]))
    elements.append(Paragraph(f"{period_label} report for {user.username}", styles["Heading2"]))
    elements.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                               styles["Normal"]))
    elements.append(Spacer(1, 0.5 * cm))

    table_data = [["Metric", "Value"]] + summary_rows
    table = Table(table_data, colWidths=[8 * cm, 8 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    elements.append(table)

    if extra_rows:
        elements.append(Spacer(1, 0.7 * cm))
        elements.append(Paragraph("Language Usage", styles["Heading3"]))
        lang_table = Table([["Language", "Time Spent"]] + extra_rows, colWidths=[8 * cm, 8 * cm])
        lang_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#059669")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
        ]))
        elements.append(lang_table)

    doc.build(elements)


def _language_rows(user_id, days):
    dist = stats_service.language_distribution(user_id, days=days)
    return [[lang, f"{secs / 3600:.1f} h"] for lang, secs in dist.items()]


@reports_bp.route("/")
@login_required
def index():
    return render_template("reports.html")


@reports_bp.route("/generate/<period>")
@login_required
def generate(period):
    user = current_user
    reports_dir = current_app.config["REPORTS_DIR"]
    os.makedirs(reports_dir, exist_ok=True)

    if period == "daily":
        s = stats_service.daily_summary(user.id)
        rows = [
            ["Coding Time", f"{s['coding_time_seconds'] / 3600:.2f} h"],
            ["Keyboard Presses", str(s["keyboard_count"])],
            ["Mouse Clicks", str(s["mouse_clicks"])],
            ["Compiles", str(s["compile_count"])],
            ["Sessions", str(s["sessions_count"])],
            ["Productivity Score", f"{s['productivity_score']}/100"],
        ]
        label, days = "Daily", 1
    elif period == "monthly":
        s = stats_service.monthly_summary(user.id)
        rows = [
            ["Total Hours (30d)", f"{s['total_hours']} h"],
            ["Average Productivity Score", f"{s['avg_score']}/100"],
            ["Active Days", str(s["days_active"])],
        ]
        label, days = "Monthly", 30
    else:
        s = stats_service.weekly_summary(user.id)
        rows = [
            ["Total Hours (7d)", f"{s['total_hours']} h"],
            ["Average Productivity Score", f"{s['avg_score']}/100"],
        ]
        label, days = "Weekly", 7

    file_name = f"{user.username}_{period}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(reports_dir, file_name)

    _build_pdf(user, label, rows, _language_rows(user.id, days), file_path)

    return send_from_directory(reports_dir, file_name, as_attachment=True)
