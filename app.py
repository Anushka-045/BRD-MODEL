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
from vertexai.generative_models import GenerativeModel
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

load_dotenv()

PROJECT_ID = "brd-model"
LOCATION = "us-central1"

vertexai.init(project=PROJECT_ID, location=LOCATION)

model_gemini = GenerativeModel("projects/236852751504/locations/us-central1/models/2536317139069960192@1")

model = joblib.load("email_classifier.pkl")
vectorizer = joblib.load("tfidf_vectorizer.pkl")

app = Flask(__name__)
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
MAX_CHARS = 8000


def filter_business_text(text):
    text_vector = vectorizer.transform([text])
    prediction = model.predict(text_vector)[0]
    if prediction == 1:
        return text
    else:
        return "No business-relevant content found."


@app.route("/")
def home():
    return "Flask + ML + Vertex Gemini is running"


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


@app.route("/upload-file", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filename = file.filename.lower()

    if filename.endswith(".txt"):
        file_content = file.read().decode("utf-8")

    elif filename.endswith(".pdf"):
        pdf_bytes = file.read()
        pdf_stream = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_stream)

        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"

        file_content = text

    elif filename.endswith(".docx"):
        document = Document(file)
        text = ""
        for para in document.paragraphs:
            text += para.text + "\n"

        file_content = text

    elif filename.endswith((".png", ".jpg", ".jpeg")):
        image = Image.open(file)
        text = pytesseract.image_to_string(image)
        file_content = text

    else:
        return jsonify({"error": "Unsupported file type"}), 400

    if len(file_content) > MAX_CHARS:
        file_content = file_content[:MAX_CHARS]

    filtered_text = filter_business_text(file_content)
    result = generate_from_text(filtered_text)

    return jsonify(result)


def generate_from_text(user_text):
    prompt = f"""
You are a professional Business Analyst.

From the following communication data:
1. Extract ONLY project-related information.
2. Ignore personal or irrelevant content.
3. Return STRICT JSON format.

JSON format:
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
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
