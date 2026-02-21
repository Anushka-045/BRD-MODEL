from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document
import io
import pandas as pd
import re
#hi
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise Exception("OPENROUTER_API_KEY not found. Check your .env file")

# Flask app setup
app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB limit
MAX_CHARS = 8000

# ---------------- Utility Functions ----------------
def clean_email(text):
    """Clean email text by removing signatures and extra newlines"""
    text = str(text)
    text = re.sub(r'-----.*?-----', '', text, flags=re.DOTALL)
    text = re.sub(r'\n+', '\n', text)
    return text.strip()

def generate_from_text(user_text):
    """Send text to OpenRouter DeepSeek API and return structured BRD JSON"""
    if len(user_text) > MAX_CHARS:
        user_text = user_text[:MAX_CHARS]

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = f"""
    You are a professional Business Analyst.

    You will receive mixed communication data such as emails, meeting notes, and chat messages.

    Tasks:
    1. Extract ONLY project-related information.
    2. Ignore personal or irrelevant content.
    3. Return the output STRICTLY in valid JSON format.
    4. Do NOT include explanations or markdown.
    5. Do NOT include ```json or any text outside JSON.
    6. If information is missing, intelligently infer reasonable business details.
    7. Do NOT leave important sections empty.
    8. If conflicting info is present, list it in "conflicts".

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

    data = {"model": "deepseek/deepseek-chat", "messages": [{"role": "user", "content": prompt}]}
    response = requests.post(url, headers=headers, json=data, timeout=30)
    result = response.json()
    print("OpenRouter response:", result)

    if "choices" not in result:
        return {"error": "AI service failed", "details": result}

    ai_reply = result["choices"][0]["message"]["content"].replace("```json", "").replace("```", "").strip()
    try:
        ai_json = json.loads(ai_reply)
    except:
        ai_json = {"error": "Invalid JSON", "raw": ai_reply}

    if isinstance(ai_json, dict):
        ai_json["functional_requirements_count"] = len(ai_json.get("functional_requirements", []))
        ai_json["stakeholder_count"] = len(ai_json.get("stakeholders", []))
        req_count = ai_json["functional_requirements_count"]
        if req_count >= 5:
            ai_json["confidence"] = "High"
        elif req_count >= 2:
            ai_json["confidence"] = "Medium"
        else:
            ai_json["confidence"] = "Low"

    return ai_json

# ---------------- Flask Routes ----------------
@app.route("/")
def home():
    return "Flask + DeepSeek BRD Generator is running"

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400

    user_text = data.get("text")
    result = generate_from_text(user_text)
    return jsonify(result)

@app.route("/upload-file", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filename = file.filename.lower()

    try:
        if filename.endswith(".txt"):
            file_content = file.read().decode("utf-8")

        elif filename.endswith(".pdf"):
            pdf_stream = io.BytesIO(file.read())
            reader = PdfReader(pdf_stream)
            file_content = "\n".join([p.extract_text() or "" for p in reader.pages])

        elif filename.endswith(".docx"):
            document = Document(file)
            file_content = "\n".join([para.text for para in document.paragraphs])

        elif filename.endswith((".png", ".jpg", ".jpeg")):
            from PIL import Image
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            image = Image.open(file)
            text = pytesseract.image_to_string(image)
            if not text.strip():
                return jsonify({"error": "No readable text found in image"}), 400
            file_content = text

        else:
            return jsonify({"error": "Unsupported file type"}), 400

        if len(file_content.strip()) == 0:
            return jsonify({"error": "No readable text found"}), 400

    except Exception as e:
        return jsonify({"error": f"Unable to read file: {str(e)}"}), 400

    result = generate_from_text(file_content)
    return jsonify(result)

@app.route("/edit", methods=["POST"])
def edit():
    data_input = request.json
    if not data_input:
        return jsonify({"error": "Invalid request"}), 400

    current_brd = data_input.get("current_brd")
    instruction = data_input.get("instruction")
    prompt = f"""
    You are a Business Analyst.
    Here is the current BRD in JSON format:
    {json.dumps(current_brd, indent=2)}
    User instruction:
    {instruction}
    Update the BRD based on the instruction.
    Return ONLY valid JSON in the same structure.
    Do not add explanations.
    """

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {"model": "deepseek/deepseek-chat", "messages": [{"role": "user", "content": prompt}]}
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=30)
    result = response.json()

    ai_reply = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    ai_reply = ai_reply.replace("```json", "").replace("```", "").strip()

    try:
        updated_json = json.loads(ai_reply)
    except:
        updated_json = {"error": "Invalid JSON", "raw": ai_reply}

    return jsonify(updated_json)

# ---------------- CSV Integration Example ----------------
@app.route("/generate-csv", methods=["POST"])
def generate_csv():
    """
    Example route to process emails.csv and generate BRDs for each row
    """
    csv_path = "data/emails.csv"
    if not os.path.exists(csv_path):
        return jsonify({"error": "emails.csv not found in data/"}), 400

    df = pd.read_csv(csv_path)
    df['Cleaned_Body'] = df['Body'].apply(clean_email)
    results = []

    for idx, email_text in enumerate(df['Cleaned_Body']):
        brd_json = generate_from_text(email_text)
        results.append({"index": idx, "brd": brd_json})

    return jsonify({"processed_count": len(results), "results": results})

# ---------------- Run App ----------------
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
