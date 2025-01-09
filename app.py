from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sklearn.ensemble import IsolationForest
from train_model import detect_anomalies


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['PDF_FOLDER'] = './pdfs'

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PDF_FOLDER'], exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"})

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"})

    if file and file.filename.endswith('.csv'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Process file for anomalies
        try:
            anomalies = process_file(filepath)
        except Exception as e:
            return jsonify({"error": str(e)})

        # Convert to JSON response
        anomalies_json = anomalies.to_dict(orient='records')

        # Generate PDF
        pdf_filename = f"anomalies_{filename.split('.')[0]}.pdf"
        pdf_filepath = os.path.join(app.config['PDF_FOLDER'], pdf_filename)
        create_pdf(anomalies, pdf_filepath)

        return jsonify({
            "anomalies": anomalies_json,
            "pdf_url": f"/download/{pdf_filename}"
        })

    return jsonify({"error": "Invalid file format"})


from sklearn.ensemble import IsolationForest  # Ensure this is imported

def process_file(filepath):
    try:
        anomalies = detect_anomalies(filepath)  # Use your trained model
    except ValueError as e:
        raise ValueError(f"Error processing file: {str(e)}")

    return anomalies[['agmtno', 'Predicted Valuation', 'NET_LOSS', 'Difference (%)', 'reason']]


def get_reason(row, columns):
    """
    Analyze the row and supporting columns to determine the likely cause of anomaly.
    """
    reasons = []

    # Check for extreme difference percentages
    if row['Difference (%)'] > 50:
        reasons.append("NET_LOSS significantly exceeds Predicted Valuation")
    elif row['Difference (%)'] < -20:
        reasons.append("Predicted Valuation is too high compared to NET_LOSS")

    # Loan-related analysis
    if 'LTV' in columns and row.get('LTV', 0) > 80:
        reasons.append("High Loan-to-Value ratio, indicating risky lending")

    # Region-related analysis
    if 'STATE' in columns and row.get('STATE') == 'Region_X':
        reasons.append("Transactions from Region_X exhibit anomalies")

    # Previous ownership analysis
    if 'PREVIOUS_OWNER_COUNT' in columns and row.get('PREVIOUS_OWNER_COUNT', 0) > 2:
        reasons.append("Asset has multiple previous owners, reducing valuation")

    return "; ".join(reasons) if reasons else "No significant anomaly"


def create_pdf(anomalies, filepath):
    c = canvas.Canvas(filepath, pagesize=letter)
    c.setFont("Helvetica", 10)

    # Set Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(200, 770, "Anomalies Report")

    # Add headers
    headers = ['Transaction ID', 'Predicted Valuation', 'NET_LOSS', 'Difference (%)', 'Reason']
    x_positions = [30, 120, 230, 340, 450]
    c.setFont("Helvetica-Bold", 10)
    for i, header in enumerate(headers):
        c.drawString(x_positions[i], 740, header)

    # Add data
    c.setFont("Helvetica", 10)
    y_position = 720
    for _, row in anomalies.iterrows():
        values = [
            str(row['agmtno']),
            f"${row['Predicted Valuation']:.2f}",
            f"${row['NET_LOSS']:.2f}",
            f"{row['Difference (%)']:.2f}%",
            row['reason']
        ]
        for i, value in enumerate(values):
            c.drawString(x_positions[i], y_position, value)
        y_position -= 20

        # Move to next page if space is insufficient
        if y_position < 50:
            c.showPage()
            y_position = 750

    c.save()


@app.route('/download/<filename>')
def download_pdf(filename):
    return send_from_directory(app.config['PDF_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
