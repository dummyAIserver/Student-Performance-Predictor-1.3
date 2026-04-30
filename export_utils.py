"""
Export utilities for Student Performance Predictor
Handles PDF and Excel export functionality
"""

import pandas as pd
import os
from datetime import datetime
from flask import send_file
import io

# Try to import reportlab, if not available, PDF export will be disabled
PDF_AVAILABLE = False
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    PDF_AVAILABLE = True
except ImportError as e:
    print(f"PDF export disabled: {e}")

# Try to import openpyxl, if not available, Excel export will be disabled
EXCEL_AVAILABLE = False
try:
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError as e:
    print(f"Excel export disabled: {e}")


def create_excel_export(history_data):
    """
    Create Excel file from history data
    """
    if not EXCEL_AVAILABLE:
        raise Exception("Excel export not available - openpyxl not installed")
    
    try:
        # Create DataFrame from history data
        df = pd.DataFrame(history_data)

        # Add performance categories
        df['Performance'] = df['prediction'].apply(categorize_performance)

        # Create Excel file in memory
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Main data sheet
            df.to_excel(writer, sheet_name='Prediction History', index=False)

            # Summary sheet
            summary_data = create_summary_stats(df)
            # Convert dict to DataFrame by wrapping in list and transposing
            summary_df = pd.DataFrame(list(summary_data.items()), columns=['Metric', 'Value'])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)

        output.seek(0)
        return output

    except Exception as e:
        raise Exception(f"Excel export failed: {str(e)}")


def create_pdf_export(history_data):
    """
    Create PDF file from history data
    """
    if not PDF_AVAILABLE:
        raise Exception("PDF export not available - reportlab not installed")
    
    try:
        # Create DataFrame
        df = pd.DataFrame(history_data)

        # Create PDF in memory
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center
        )
        story.append(Paragraph("Student Performance Prediction History", title_style))

        # Date
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1
        )
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", date_style))
        story.append(Spacer(1, 20))

        # Summary Statistics
        summary = create_summary_stats(df)
        story.append(Paragraph("Summary Statistics", styles['Heading2']))
        story.append(Spacer(1, 12))

        summary_data = []
        for key, value in summary.items():
            summary_data.append([key, str(value)])

        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))

        # Detailed History Table
        story.append(Paragraph("Detailed Prediction History", styles['Heading2']))
        story.append(Spacer(1, 12))

        # Prepare table data
        table_data = [['Student Name', 'Attendance', 'Assignment', 'Internal', 'Predicted', 'Grade', 'Performance']]
        for _, row in df.iterrows():
            performance = categorize_performance(row['prediction'])
            student_name = row.get('student_name', 'Unknown')
            grade = row.get('grade', '-')
            table_data.append([
                str(student_name),
                f"{row['attendance']:.1f}%",
                f"{row['assignment_score']:.1f}",
                f"{row['internal_marks']:.1f}",
                f"{row['prediction']:.2f}",
                str(grade),
                performance
            ])

        # Create table
        table = Table(table_data, colWidths=[1.2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.6*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Left align Student Name column
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9)
        ]))

        story.append(table)

        # Build PDF
        doc.build(story)
        output.seek(0)
        return output

    except Exception as e:
        raise Exception(f"PDF export failed: {str(e)}")


def categorize_performance(score):
    """
    Categorize performance based on score
    """
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Average"
    else:
        return "Needs Improvement"


def create_summary_stats(df):
    """
    Create summary statistics from DataFrame
    """
    if len(df) == 0:
        return {
            'Total Predictions': 0,
            'Average Score': 0,
            'Highest Score': 0,
            'Lowest Score': 0,
            'Excellent Performance': 0,
            'Good Performance': 0,
            'Average Performance': 0,
            'Needs Improvement': 0
        }

    return {
        'Total Predictions': len(df),
        'Average Score': round(df['prediction'].mean(), 2),
        'Highest Score': round(df['prediction'].max(), 2),
        'Lowest Score': round(df['prediction'].min(), 2),
        'Excellent Performance': len(df[df['prediction'] >= 80]),
        'Good Performance': len(df[(df['prediction'] >= 60) & (df['prediction'] < 80)]),
        'Average Performance': len(df[(df['prediction'] >= 40) & (df['prediction'] < 60)]),
        'Needs Improvement': len(df[df['prediction'] < 40])
    }


def generate_filename(format_type):
    """
    Generate filename with timestamp
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"student_performance_history_{timestamp}.{format_type}"
