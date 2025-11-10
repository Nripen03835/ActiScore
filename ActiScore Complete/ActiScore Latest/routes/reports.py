from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required, current_user
from database.db import db, Analysis, User
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from datetime import datetime
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import json

reports = Blueprint('reports', __name__)

@reports.route('/generate-report', methods=['POST'])
@login_required
def generate_report():
    """Generate a report based on analysis data"""
    try:
        data = request.json
        report_type = data.get('type', 'pdf')
        analysis_ids = data.get('analysis_ids', [])
        template = data.get('template', 'default')
        
        # Get analyses data
        analyses = Analysis.query.filter(Analysis.id.in_(analysis_ids)).all()
        
        if not analyses:
            return jsonify({'error': 'No analyses found'}), 404
        
        # Generate report based on type
        if report_type == 'pdf':
            return generate_pdf_report(analyses, template)
        elif report_type == 'excel':
            return generate_excel_report(analyses)
        elif report_type == 'ppt':
            return generate_ppt_report(analyses, template)
        else:
            return jsonify({'error': 'Unsupported report type'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_pdf_report(analyses, template):
    """Generate PDF report from analyses"""
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Add title
    title_style = styles['Title']
    elements.append(Paragraph("ActiScore Emotion Analysis Report", title_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add date
    date_style = styles['Normal']
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", date_style))
    elements.append(Paragraph(f"User: {current_user.username}", date_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add summary
    elements.append(Paragraph("Summary of Analyses", styles['Heading2']))
    elements.append(Spacer(1, 0.1*inch))
    
    # Create summary table
    summary_data = [['Date', 'Type', 'Duration', 'Dominant Emotion']]
    for analysis in analyses:
        results = json.loads(analysis.results)
        summary_data.append([
            analysis.created_at.strftime('%Y-%m-%d %H:%M'),
            analysis.analysis_type,
            f"{results.get('duration', 0):.1f} seconds",
            results.get('dominant_emotion', 'Unknown')
        ])
    
    summary_table = Table(summary_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.25*inch))
    
    # Add detailed analysis for each item
    elements.append(Paragraph("Detailed Analysis", styles['Heading2']))
    elements.append(Spacer(1, 0.1*inch))
    
    for analysis in analyses:
        results = json.loads(analysis.results)
        elements.append(Paragraph(f"Analysis ID: {analysis.id}", styles['Heading3']))
        elements.append(Paragraph(f"Date: {analysis.created_at.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        elements.append(Paragraph(f"Type: {analysis.analysis_type}", styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Add emotion data
        if 'emotions' in results:
            emotions_data = [['Emotion', 'Confidence']]
            for emotion, score in results['emotions'].items():
                emotions_data.append([emotion, f"{score:.2f}"])
            
            emotions_table = Table(emotions_data, colWidths=[2*inch, 2*inch])
            emotions_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(emotions_table)
        
        # Add chart if available
        if 'chart_image' in results:
            img_data = base64.b64decode(results['chart_image'])
            img = Image(io.BytesIO(img_data), width=6*inch, height=3*inch)
            elements.append(img)
        
        elements.append(Spacer(1, 0.25*inch))
    
    # Build PDF
    doc.build(elements)
    
    # Prepare response
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"actiscore_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mimetype='application/pdf'
    )

def generate_excel_report(analyses):
    """Generate Excel report from analyses"""
    buffer = io.BytesIO()
    
    # Create Excel writer
    writer = pd.ExcelWriter(buffer, engine='xlsxwriter')
    
    # Create summary sheet
    summary_data = []
    for analysis in analyses:
        results = json.loads(analysis.results)
        summary_data.append({
            'ID': analysis.id,
            'Date': analysis.created_at,
            'Type': analysis.analysis_type,
            'Duration': results.get('duration', 0),
            'Dominant Emotion': results.get('dominant_emotion', 'Unknown')
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    # Create detailed sheets for each analysis
    for i, analysis in enumerate(analyses):
        results = json.loads(analysis.results)
        
        if 'emotions' in results:
            emotions_data = []
            for emotion, score in results['emotions'].items():
                emotions_data.append({
                    'Emotion': emotion,
                    'Confidence': score
                })
            
            emotions_df = pd.DataFrame(emotions_data)
            emotions_df.to_excel(writer, sheet_name=f'Analysis_{i+1}', index=False)
    
    # Save Excel file
    writer.save()
    
    # Prepare response
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"actiscore_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def generate_ppt_report(analyses, template):
    """Generate PowerPoint report from analyses"""
    # This would use python-pptx library to create PowerPoint presentations
    # For simplicity, we'll return a placeholder response
    return jsonify({
        'message': 'PowerPoint report generation is not implemented in this demo',
        'analyses': [a.id for a in analyses],
        'template': template
    })

@reports.route('/report-templates', methods=['GET'])
@login_required
def get_report_templates():
    """Get available report templates"""
    templates = [
        {
            'id': 'default',
            'name': 'Default Template',
            'description': 'Standard report with summary and detailed analysis',
            'thumbnail': '/static/images/templates/default.png'
        },
        {
            'id': 'executive',
            'name': 'Executive Summary',
            'description': 'Concise report focused on key metrics and insights',
            'thumbnail': '/static/images/templates/executive.png'
        },
        {
            'id': 'detailed',
            'name': 'Detailed Analysis',
            'description': 'Comprehensive report with in-depth analysis and visualizations',
            'thumbnail': '/static/images/templates/detailed.png'
        },
        {
            'id': 'comparison',
            'name': 'Comparison Report',
            'description': 'Side-by-side comparison of multiple analyses',
            'thumbnail': '/static/images/templates/comparison.png'
        },
        {
            'id': 'timeline',
            'name': 'Timeline Report',
            'description': 'Chronological analysis showing emotion changes over time',
            'thumbnail': '/static/images/templates/timeline.png'
        }
    ]
    
    return jsonify(templates)