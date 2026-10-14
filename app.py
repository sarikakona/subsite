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

    # Extract raw text line-by-line from the PDF
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"

    # Scan text for known vendors, dates, and amounts
    lines = extracted_text.split("\n")
    for line in lines:
        for vendor in KNOWN_SUBSCRIPTIONS:
            if vendor.lower() in line.lower():
                price_match = re.search(r'\$?\b\d+\.\d{2}\b', line)
                date_match = re.search(r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2})\b', line)
                
                cost = price_match.group(0) if price_match else "0.00"
                billing_date = date_match.group(0) if date_match else "N/A"

                found_subscriptions.append({
                    "serviceName": vendor,
                    "cost": float(cost.replace("$", "")),
                    "nextBillingDate": billing_date,
                    "category": "Detected Subscription"
                })

    return found_subscriptions

@app.route('/parse-bill', methods=['POST'])
def parse_bill_endpoint():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    file_path = f"/tmp/{file.filename}"
    file.save(file_path)

    parsed_data = parse_pdf_for_subscriptions(file_path)
    return jsonify({"subscriptions": parsed_data}), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)
