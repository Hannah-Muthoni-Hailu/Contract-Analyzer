from flask import Flask, request, jsonify
from flask_cors import CORS
from huggingface_hub import InferenceClient
import nltk
import pdfplumber
nltk.download('punkt_tab')
import os
import json
from gradio_client import Client
import webbrowser
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app)  # Allow React frontend to communicate with Flask backend

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

client_token = os.getenv("INFERENCE_CLIENT_TOKEN")

client = InferenceClient(token=client_token)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], "submitted_file.pdf")
    file.save(filepath)
    
    text = ''
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            text += page.extract_text()

    text = text.strip()

    # Create short summary
    short = short_summary(text)

    # Create long summary
    long = long_summary(text)

    # Predict labels
    predictions = predict_labels(text)
    questions = {
        'Agreement Date' : 'Does the specified agreement date work for you?', 
        'Effective Date' : 'Is the expiration date suitable for your needs?', 
        'Expiration Date' : 'Is the expiration date suitable for your needs?', 
        'Renewal Term' : 'Are you agreeable to the proposed renewal term?', 
        'Notice Period To Terminate Renewal' : 'Is the notice period for terminating the renewal sufficient for you?', 
        'Governing Law' : 'Do you agree with the governing law stipulated in the agreement?', 
        'Most Favored Nation' : 'Do you accept the terms of the most-favored-nation clause?', 
        'Competitive Restriction Exception' : 'Are the listed exceptions to competitive restrictions acceptable?', 
        'Non-Compete' : 'Do you agree to the non-compete terms?', 
        'Exclusivity' : 'Do you accept the exclusivity terms outlined in the agreement?', 
        'No-Solicit Of Customers' : 'Do you agree not to solicit the other party\'s customers?', 
        'No-Solicit Of Employees' : 'Are you in agreement with the no-solicit-of-employees clause?', 
        'Non-Disparagement' : 'Will you adhere to the non-disparagement clause?', 
        'Termination For Convenience' : 'Do you accept the termination-for-convenience terms?', 
        'Change Of Control' : 'Are you agreeable to the terms related to change of control?', 
        'Anti-Assignment'  : 'Do you agree with the anti-assignment clause?', 
        'Revenue/Profit Sharing' : 'Do the revenue/profit-sharing terms meet your expectations?', 
        'Price Restrictions' : 'Are the proposed price restrictions acceptable to you?', 
        'Minimum Commitment' : 'Do you agree to the minimum commitment requirements?', 
        'Volume Restriction' : 'Are the volume restriction terms acceptable?', 
        'Ip Ownership Assignment' : 'Do you agree to assign ownership of the intellectual property as outlined?', 
        'Joint Ip Ownership' : 'Are the terms for joint intellectual property ownership acceptable?', 
        'License Grant' : 'Do you agree with the scope of the license granted?', 
        'Non-Transferable License' : 'Do you accept that the license is non-transferable?', 
        'Affiliate License-Licensor' : 'Are you comfortable with the affiliate license terms for the licensor?', 
        'Affiliate License-Licensee' : 'Are the affiliate license terms for the licensee acceptable to you?', 
        'Unlimited/All-You-Can-Eat-License' : 'Do you accept the terms of the unlimited license?', 
        'Irrevocable Or Perpetual License' : 'Are the terms for an irrevocable or perpetual license agreeable?', 
        'Source Code Escrow' : 'Do you accept the source code escrow terms?', 
        'Post-Termination Services' : 'Are you comfortable with the post-termination services provisions?', 
        'Audit Rights' : 'Do you agree to the audit rights outlined in the agreement?', 
        'Uncapped Liability' : 'Are you comfortable with the uncapped liability clause?', 
        'Cap On Liability' : 'Is the liability cap acceptable to you?', 
        'Liquidated Damages' : 'Do you agree with the liquidated damages terms?', 
        'Warranty Duration' : 'Is the proposed warranty duration acceptable?', 
        'Insurance' : 'Are the insurance requirements agreeable to you?', 
        'Covenant Not To Sue' : 'Do you agree to the covenant not to sue?', 
        'Third Party Beneficiary'  : 'Do you accept the inclusion of a third-party beneficiary clause?'
    }

    result_questions = []

    for item in predictions:
        result_questions.append([item['label'], questions[item['label']], item['text']])

    return jsonify({
        "short-summary": short,
        "long-summary": long,
        "help": result_questions,
        "file_path": filepath
    })

@app.route('/submit-form', methods=['POST'])
def submit_form():
    data = request.json.get('answers', [])
    counter = 0
    total = 0
    mismatches = []

    for entry in data:
        if entry['response'] == "yes":
            counter += 1
        else:
            mismatches.append(entry['question'])
        total += 1

    avg = (counter / total) * 100

    if avg == 100:
        analysis = "good"
    else:
        analysis = "poor"

    

    response = {
        'message': mismatches,
        'analysis': analysis
        }
    return jsonify(response)

def predict_labels(contract_text):
    text = contract_text.replace("\n", " ").strip()

    client = Client("louiseclon3/contract-labeler")
    result = client.predict(contract_text=text,api_name="/predict")
    return result

def short_summary(text):
    response = client.post(json={"inputs":text}, model="google/pegasus-xsum")

    result = json.loads(response.decode("utf-8"))
    
    # Extract the summary_text field
    summary = result[0]["summary_text"]
    
    return summary

def long_summary(text):
    text = text.replace("\n", " ").strip()

    client = Client("louiseclon3/legal-doc-labeler")
    result = client.predict(text=text,api_name="/predict")
    
    return result

@app.route('/create-signing-url', methods=['POST'])
def create_signing_url():
    webbrowser.open("http://localhost:3000")
    return "Done"

if __name__ == '__main__':
    app.run(port=5000)