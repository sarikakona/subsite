import re
import pdfplumber
from flask import Flask, request, jsonify

app = Flask(__name__)

# Standard recurring subscription vendor database to match against
KNOWN_SUBSCRIPTIONS = [
    "Netflix", "Spotify", "Adobe", "AWS", "Amazon Prime", 
    "Hulu", "Disney+", "Apple", "Google One", "LinkedIn"
]

def parse_pdf_for_subscriptions(pdf_path):
    extracted_text = ""
    found_subscriptions = []

    # 1. Extract raw text line-by-line from the PDF
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"

    # 2. Extract Statement Month/Year (e.g., "October 2026" or "10/2026")
    date_header_match = re.search(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b', extracted_text, re.IGNORECASE)
    statement_period = date_header_match.group(0) if date_header_match else "Oct 2026"

    # 3. Scan text for known vendors, dates, and amounts
    lines = extracted_text.split("\n")
    for line in lines:
        for vendor in KNOWN_SUBSCRIPTIONS:
            if vendor.lower() in line.lower():
                price_match = re.search(r'\$?\b\d+\.\d{2}\b', line)
                cost = price_match.group(0) if price_match else "0.00"

                found_subscriptions.append({
                    "serviceName": vendor,
                    "cost": float(cost.replace("$", "")),
                    "statementPeriod": statement_period,
                    "category": "Software" if vendor in ["Adobe", "AWS"] else "Entertainment"
                })

    return found_subscriptions, statement_period

@app.route('/parse-bill', methods=['POST'])
def parse_bill_endpoint():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    file_path = f"/tmp/{file.filename}"
    file.save(file_path)

    parsed_data, period = parse_pdf_for_subscriptions(file_path)
    return jsonify({
        "subscriptions": parsed_data,
        "statementPeriod": period
    }), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)
