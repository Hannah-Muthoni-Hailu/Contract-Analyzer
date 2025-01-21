from flask import Flask, request, jsonify, redirect
import requests
from flask_cors import CORS
from huggingface_hub import InferenceClient
import nltk
import pdfplumber
nltk.download('punkt_tab')
import os
import json
from gradio_client import Client
from dotenv import load_dotenv
import base64
import hashlib
import urllib.parse
load_dotenv()

app = Flask(__name__)
CORS(app)  # Allow React frontend to communicate with Flask backend

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
FILE_PATH = None
FILE_NAME = None
SIGNER_NAME = None
SIGNER_EMAIL = None

client_token = os.getenv("INFERENCE_CLIENT_TOKEN")
client = InferenceClient(token=client_token)

CLIENT_ID = os.getenv("DOCUSIGN_CLIENT_ID")
REDIRECT_URI = os.getenv("DOCUSIGN_REDIRECT_URI")
END_URI = os.getenv("PROCESS_COMPLETE_URI")
ACCOUNT_ID = os.getenv("DOCUSIGN_ACCOUNT_ID")
AUTH_URL = "https://account-d.docusign.com/oauth/auth"
TOKEN_URL = "https://account-d.docusign.com/oauth/token"
code_verifier = base64.urlsafe_b64encode(os.urandom(64)).rstrip(b"=").decode("utf-8")
code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode("utf-8")).digest()).rstrip(b"=").decode("utf-8")
ORIGIN = "https://contract-analyzer-backend-etzi.onrender.com"
DOCUSIGN_API_URL = "https://demo.docusign.net/restapi"  # Use "https://www.docusign.com/restapi" for production
ENVELOPE_API_URL = f"{DOCUSIGN_API_URL}/v2.1/accounts/{ACCOUNT_ID}/envelopes"


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], "submitted_file.pdf")
    file.save(filepath)

    global FILE_PATH, FILE_NAME, SIGNER_NAME, SIGNER_EMAIL
    FILE_PATH = filepath
    FILE_NAME = file.filename
    SIGNER_NAME = request.form.get('signer_name')
    SIGNER_EMAIL = request.form.get('signer_email')

    if not SIGNER_NAME or not SIGNER_EMAIL:
        return jsonify({"error": "Signer name and email are required"}), 400
    
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

@app.route('/create-signing-url')
def create_signing_url():
    auth_endpoint = (f"{AUTH_URL}?response_type=code&scope=signature&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&code_challenge={code_challenge}&code_challenge_method=S256")
    return redirect(auth_endpoint)

@app.route("/callback")
def callback():
    code = request.args.get("code")

    if not code:
        return "Authorization code not found", 400

    # Exchange authorization code for an access token
    token_response = requests.post(
        TOKEN_URL,
        headers={"Origin": ORIGIN},  # Include Origin header if required
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": code_verifier,
            "client_id": CLIENT_ID,
        },
    )

    if token_response.status_code == 200:
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        global FILE_PATH, FILE_NAME, SIGNER_NAME, SIGNER_EMAIL

        # Create the envelope
        envelope_id = create_envelope(
            access_token=access_token,
            file_path=FILE_PATH,
            file_name=FILE_NAME,
            signer_name=SIGNER_NAME,
            signer_email=SIGNER_EMAIL,
        )

        if not envelope_id:
            return "Failed to create envelope", 400

        # Create the recipient view (signing URL)
        signing_url = create_recipient_view(
            access_token=access_token,
            account_id=ACCOUNT_ID,
            envelope_id=envelope_id,
            signer_name=SIGNER_NAME,
            signer_email=SIGNER_EMAIL,
            return_url=END_URI,
        )

        if signing_url:
            redirect_url = f"https://contract-analyzer-uw74.onrender.com/sign?signing_url={urllib.parse.quote(signing_url)}"
            return redirect(redirect_url)
        else:
            return "Failed to create recipient view", 400
    else:
        return f"Failed to get access token: {token_response.text}", 400

def create_envelope(access_token, file_path, file_name, signer_name, signer_email):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    # Prepare the document
    with open(file_path, 'rb') as document:
        file_data = document.read()

    encoded_file = base64.b64encode(file_data).decode('utf-8')

    # Define envelope structure
    envelope_data = {
        "status": "sent",
        "emailSubject": "Please sign this document",
        "documents": [
            {
                "documentBase64": encoded_file,
                "name": file_name,
                "fileExtension": "pdf",
                "documentId": "1",
            }
        ],
        "recipients": {
            "signers": [
                {
                    "email": signer_email,
                    "name": signer_name,
                    "recipientId": "1",
                    "clientUserId": "12345",
                    "routingOrder": "1",
                    "tabs": {
                        "signHereTabs": [
                            {
                                "xPosition": "100",
                                "yPosition": "100",
                                "documentId": "1",
                                "pageNumber": "1",
                            }
                        ]
                    },
                }
            ]
        },
    }

    response = requests.post(
        ENVELOPE_API_URL, headers=headers, json=envelope_data
    )

    if response.status_code == 201:
        return response.json().get("envelopeId")
    else:
        print(f"Failed to create envelope: {response.text}")
        return None

def create_recipient_view(access_token, account_id, envelope_id, signer_name, signer_email, return_url):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    url = f"https://demo.docusign.net/restapi/v2.1/accounts/{account_id}/envelopes/{envelope_id}/views/recipient"

    data = {
        "authenticationMethod": "none",
        "email": signer_email,
        "userName": signer_name,
        "clientUserId": "12345",
        "returnUrl": return_url,
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        return response.json().get("url")
    else:
        print(f"Failed to create recipient view: {response.text}")
        return None
   
if __name__ == '__main__':
    app.run(port=5000)
