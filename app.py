from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document
import pytesseract
import io
from PIL import Image
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise Exception("OPENROUTER_API_KEY not found. Check your .env file")
app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  
MAX_CHARS = 8000
@app.route("/")
def home():
    return "Flask+DEEPSEEK is running"
@app.route("/generate",methods=["POST"])
def generate():
    data = request.json
    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400

    user_text = data.get("text")
    if len(user_text) > MAX_CHARS:
        user_text = user_text[:MAX_CHARS]
    result = generate_from_text(user_text)
    return jsonify(result)
@app.route("/upload-file", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filename = file.filename.lower()

    
    if filename.endswith(".txt"):
        try:
            file_content = file.read().decode("utf-8")
        except:
            return jsonify({"error": "Unable to read TXT file"}), 400

    
    elif filename.endswith(".pdf"):
        try:
            pdf_bytes = file.read()
            pdf_stream = io.BytesIO(pdf_bytes)
            reader = PdfReader(pdf_stream)

            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"

            if not text.strip():
                return jsonify({"error": "PDF has no readable text"}), 400

            
            if len(text) > MAX_CHARS:
                text = text[:MAX_CHARS]

            file_content = text

        except Exception as e:
            return jsonify({"error": f"Unable to read PDF: {str(e)}"}), 400

    
    elif filename.endswith(".docx"):
        try:
            document = Document(file)
            text = ""
            for para in document.paragraphs:
                text += para.text + "\n"

            if not text.strip():
                return jsonify({"error": "DOCX has no readable text"}), 400

            file_content = text

        except Exception as e:
            return jsonify({"error": f"Unable to read DOCX: {str(e)}"}), 400
    elif filename.endswith((".png", ".jpg", ".jpeg")):
        try:
            image = Image.open(file)
            text = pytesseract.image_to_string(image)
            if not text.strip():
                return jsonify({"error": "No readable text found in image"}), 400
            file_content = text
        except Exception as e:
            return jsonify({"error": f"Unable to read image: {str(e)}"}), 400
    else:
        return jsonify({"error": "Unsupported file type. Allowed: txt, pdf, docx, png, jpg, jpeg"}), 400

    result = generate_from_text(file_content)
    return jsonify(result)
@app.route("/edit",methods=["POST"])
def edit():
    data_input = request.json
    if not data_input:
        return jsonify({"error": "Invalid request"}), 400

    current_brd = data_input.get("current_brd")
    instruction = data_input.get("instruction")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type" : "application/json"
    }
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
    data = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    response = requests.post(url, headers=headers, json=data, timeout=30)
    result = response.json()
    print("OpenRouter response:", result)
    if "choices" not in result:
        return jsonify({"error": "AI service failed", "details": result})
    ai_reply = result["choices"][0]["message"]["content"]
    ai_reply = ai_reply.replace("```json", "").replace("```", "").strip()

    try:
        updated_json = json.loads(ai_reply)
    except:
        updated_json = {"error": "Invalid JSON", "raw": ai_reply}

    return jsonify(updated_json)
def generate_from_text(user_text):
    url = "https://openrouter.ai/api/v1/chat/completions"
    if len(user_text) > MAX_CHARS:
        user_text = user_text[:MAX_CHARS]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = f"""
    You are a professional Business Analyst.

    You will receive mixed communication data such as emails, meeting notes, and chat messages.

    Tasks:
    From the following communication data (emails, meetings, chats):
    1. Extract ONLY project-related information.
    2. Ignore personal or irrelevant content.
    3. Return the output STRICTLY in valid JSON format.
    4. Do NOT include explanations or markdown.
    5. Do NOT include ```json or any text outside JSON.
    6.If some information is missing, intelligently infer reasonable business details.
    7.Do NOT leave important sections empty.
    8.If conflicting information is present (for example different timelines, different requirements, or contradictory statements), list them in a field called "conflicts".
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
    {user_text}"""

    data = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(url, headers=headers, json=data, timeout=30)
    result = response.json()
    print("OpenRouter response:", result)

    if "choices" not in result:
        return {"error": "AI service failed", "details": result}
    ai_reply = result["choices"][0]["message"]["content"]
    ai_reply = ai_reply.replace("```json", "").replace("```", "").strip()

    try:
        ai_json = json.loads(ai_reply)
    except:
        ai_json = {"error": "Invalid JSON", "raw": ai_reply}
    if isinstance(ai_json, dict):
        ai_json["functional_requirements_count"] = len(ai_json.get("functional_requirements", []))
        ai_json["stakeholder_count"] = len(ai_json.get("stakeholders", []))
    req_count = ai_json.get("functional_requirements_count", 0)
    if req_count >= 5:
        ai_json["confidence"] = "High"
    elif req_count >= 2:
        ai_json["confidence"] = "Medium"
    else:
        ai_json["confidence"] = "Low"
    return ai_json
    
if __name__ =="__main__":
    app.run(debug=True,use_reloader=False)