from weasyprint import HTML
from flask import render_template
from datetime import datetime
import os

def export_health_report_pdf(user_name, history_data, ai_report, output_path, summary=None):
    """
    渲染 report_template.html 并导出 PDF
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    html_content = render_template(
        'report_template.html',
        user_name=user_name,
        history=history_data,
        ai_report=ai_report,
        summary=summary,
        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M')
    )

    HTML(string=html_content).write_pdf(output_path)
    return output_path
