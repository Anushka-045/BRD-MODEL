from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document
import io
from PIL import Image
import joblib
import vertexai
from vertexai.preview.generative_models import GenerativeModel
import pytesseract
from google.oauth2 import service_account

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()

PROJECT_ID = "brd-model"
LOCATION = "us-central1"

# ----------------------------
# Vertex AI Authentication
# ----------------------------
credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")

if credentials_json:
    credentials_info = json.loads(credentials_json)
    credentials = service_account.Credentials.from_service_account_info(
        credentials_info
    )
    vertexai.init(
        project=PROJECT_ID,
        location=LOCATION,
        credentials=credentials
    )
else:
    # Local development fallback
    vertexai.init(
        project=PROJECT_ID,
        location=LOCATION
    )

# ----------------------------
# Load Tuned Gemini Model
# ----------------------------
model_gemini = GenerativeModel("brd-gemini-tuned")

# ----------------------------
# Load ML Classifier
# ----------------------------
model = joblib.load("email_classifier.pkl")
vectorizer = joblib.load("tfidf_vectorizer.pkl")

# ----------------------------
# Flask App Setup
# ----------------------------
app = Flask(__name__)
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
MAX_CHARS = 8000

# ----------------------------
# Tesseract Path Fix
# ----------------------------
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


# ----------------------------
# Business Text Filter
# ----------------------------
def filter_business_text(text):
    text_vector = vectorizer.transform([text])
    prediction = model.predict(text_vector)[0]
    if prediction == 1:
        return text
    else:
        return "No business-relevant content found."


# ----------------------------
# Home Route
# ----------------------------
@app.route("/")
def home():
    return "Flask + ML + Tuned Gemini is running"


# ----------------------------
# Generate Route
# ----------------------------
@app.route("/generate", methods=["POST"])
def generate():
    data = request.json

    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400

    user_text = data.get("text")

    if len(user_text) > MAX_CHARS:
        user_text = user_text[:MAX_CHARS]

    filtered_text = filter_business_text(user_text)
    result = generate_from_text(filtered_text)

    return jsonify(result)


# ----------------------------
# File Upload Route
# ----------------------------
# ----------------------------
# Gemini Generator Function
# ----------------------------
def generate_from_text(user_text):
    prompt = f"""
You are a professional Business Analyst.

Return STRICT JSON:
{{
    "executive_summary": "",
    "business_objectives": [],
    "stakeholders": [],
    "functional_requirements": [],
    "non_functional_requirements": [],
    "assumptions": [],
    "timeline": "",
    "conflicts": []
}}

Communication Data:
{user_text}
"""

    try:
        response = model_gemini.generate_content(prompt)
        text_response = response.text.strip()

        text_response = text_response.replace("```json", "").replace("```", "").strip()

        return json.loads(text_response)

    except Exception as e:
        return {"error": str(e)}


# ----------------------------
# Run App
# ----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
