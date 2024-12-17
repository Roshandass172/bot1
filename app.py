from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from train_model import detect_anomalies

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['PDF_FOLDER'] = './pdfs'  # Folder to store PDFs

# Ensure the PDFs folder exists
os.makedirs(app.config['PDF_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '').lower()
    # Sample intents
    if 'hello' in user_message:
        response = "Hello! How can I assist you today?"
    elif 'fraud' in user_message:
        response = "You can upload a CSV file for fraud detection below."
    else:
        response = "I'm sorry, I don't understand. Could you rephrase?"
    return jsonify({'response': response})

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

        anomalies = detect_anomalies(filepath)

        # Convert DataFrame to a list of dictionaries for JSON response
        anomalies_json = anomalies.to_dict(orient='records')

        # Generate PDF
        pdf_filename = f"anomalies_{filename.split('.')[0]}.pdf"
        pdf_filepath = os.path.join(app.config['PDF_FOLDER'], pdf_filename)
        create_pdf(anomalies, pdf_filepath)

        return jsonify({
            "anomalies": anomalies_json,
            "pdf_url": f"/download/{pdf_filename}"  # Provide the link to download the PDF
        })

    return jsonify({"error": "Invalid file format"})


def create_pdf(anomalies, filepath):
    c = canvas.Canvas(filepath, pagesize=letter)
    c.setFont("Helvetica", 10)
    
    # Set Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(200, 770, "Anomalies Report")

    # Add headers
    c.setFont("Helvetica-Bold", 10)
    c.drawString(30, 740, "Transaction ID")
    c.drawString(150, 740, "Amount")
    c.drawString(270, 740, "Anomaly")
    c.drawString(380, 740, "Timestamp")

    # Add data
    c.setFont("Helvetica", 10)
    y_position = 720
    for anomaly in anomalies.itertuples():
        c.drawString(30, y_position, str(anomaly.transaction_id))
        c.drawString(150, y_position, f"${anomaly.amount}")
        c.drawString(270, y_position, str(anomaly.anomaly))
        c.drawString(380, y_position, str(anomaly.timestamp))
        y_position -= 20

    c.save()

@app.route('/download/<filename>')
def download_pdf(filename):
    return send_from_directory(app.config['PDF_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
