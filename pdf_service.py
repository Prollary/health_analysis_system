from weasyprint import HTML
from flask import render_template
import os

def export_health_report_pdf(user_name, history_data, ai_report, output_path):
    """
    渲染 HTML 并导出 PDF
    """
    # 这里假设你有一个 templates/report_template.html
    html_content = render_template(
        'report_template.html',
        user_name=user_name,
        history=history_data,
        ai_report=ai_report
    )
    
    # 导出 PDF
    HTML(string=html_content).write_pdf(output_path)
    return output_path