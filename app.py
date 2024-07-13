from flask import Flask, request, send_file, render_template, jsonify
import pandas as pd
import io
import json
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

app = Flask(__name__)

# Function to read logs safely
def read_logs():
    if os.path.exists('log.json'):
        try:
            with open('log.json', 'r') as f:
                logs = json.load(f)
            return logs
        except (json.JSONDecodeError, IOError):
            return []
    return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-invoice', methods=['POST'])
def generate_invoice():
    data = request.json

    # Extract and format additional fields
    bill_to = data.get('bill_to', '')
    invoice_number = data.get('invoice_number', '')
    date = data.get('date', '')

    # Create a DataFrame with the remaining data
    invoice_data = {
        'date': [data.get('date', '')],
        'ticket': [data.get('ticket', '')],
        'truck': [data.get('truck', '')],
        'hours': [data.get('hours', 0)],
        'price': [data.get('price', 0)],
        'location': [data.get('location', '')]
    }

    df = pd.DataFrame(invoice_data)
    df["Total"] = df["hours"].astype(int) * df["price"].astype(int)
    total_hours = df["hours"].sum()
    total_amount = df["Total"].sum()
    
    # Create a PDF
    output = io.BytesIO()
    p = canvas.Canvas(output, pagesize=letter)
    width, height = letter

    styles = getSampleStyleSheet()
    margin = 30

    # Add company information header
    company_info = """
        <para align=center spaceb=3>
        <b>JO TRUCKING LLC</b><br/>
        213 North 16TH ST<br/>
        Bloomfield, NJ 07003<br/>
        Tel: (973)288-55022 / (973)336-7692
        </para>
    """
    company_info_paragraph = Paragraph(company_info, styles['Normal'])
    company_info_paragraph.wrapOn(p, width - 2 * margin, height)
    company_info_paragraph.drawOn(p, margin, height - 100)
    
    # Add Bill To and Invoice information
    p.drawString(margin, height - 140, f'Bill To:')
    bill_to_paragraph = Paragraph(bill_to, styles['Normal'])
    bill_to_paragraph.wrapOn(p, width - 2 * margin, height)
    bill_to_paragraph.drawOn(p, margin, height - 160)
    p.drawString(width - 200, height - 140, f'Invoice: {invoice_number}')
    p.drawString(width - 200, height - 160, f'Date: {date}')

    # Define a bold style for the table header
    bold_style = ParagraphStyle(name='Bold', parent=styles['Normal'], fontName='Helvetica-Bold')

    # Add table header with bold text
    table_data = [
        [
            Paragraph('Date', bold_style),
            Paragraph('Ticket', bold_style),
            Paragraph('Truck #', bold_style),
            Paragraph('Hours', bold_style),
            Paragraph('Price Per Hour', bold_style),
            Paragraph('Total', bold_style),
            Paragraph('Location', bold_style)
        ]
    ]
    
    # Add rows to the table
    for index, row in df.iterrows():
        table_data.append([
            str(row['date']),
            str(row['ticket']),
            str(row['truck']),
            str(row['hours']),
            str(row['price']),
            str(row['Total']),
            Paragraph(str(row['location']), styles['Normal'])
        ])
    
    # Add summary row
    table_data.append(['', '', '', f'Total Hours: {total_hours}', '', f'Total: {total_amount}', ''])
    
    # Create the table
    col_widths = [(width - 2 * margin) / 7] * 7  # Adjust column widths to fill the page width with margins
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.transparent),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.transparent),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('WORDWRAP', (0, 0), (-1, -1), 'LTR')
    ]))

    # Calculate the table width and position it with margins
    table.wrapOn(p, width, height)
    table.drawOn(p, margin, height - 300)  # Adjust the position to account for the wrapped Bill To text
    
    p.showPage()
    p.save()
    
    output.seek(0)

    # Log the document creation
    log_entry = {
        "filename": "invoice.pdf",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    logs = read_logs()
    logs.append(log_entry)
    with open('log.json', 'w') as f:
        json.dump(logs, f)

    return send_file(output, download_name='invoice.pdf', as_attachment=True, mimetype='application/pdf')

@app.route('/get-logs', methods=['GET'])
def get_logs():
    logs = read_logs()
    return jsonify(logs)

if __name__ == '__main__':
    app.run(debug=True)
