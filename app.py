import os
import json
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

# --- Configuration ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDALevog6Y6bJRbYlygpZx_ORGkE2L7Wos")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "sk_77adeab28c459eead0a9267e9063585c9ce8a1feafbb6ecd")
PRIMARY_VOICE_ID = "oWAO0WajY0pX9AlCD9V7"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
chat = model.start_chat(history=[])

# Servers root, child folders or current - search index.html
def get_file_path(filename):
    # Try current directory
    if os.path.exists(filename): return ".", filename
    # Try web_content folder
    if os.path.exists(os.path.join("web_content", filename)): return "web_content", filename
    return None, None

@app.route('/')
def index():
    path, file = get_file_path("index.html")
    if path: return send_from_directory(path, file)
    return "<h1>Mira Error: index.html not found!</h1><p>Please make sure index.html is in the main folder or web_content folder.</p>", 404

@app.route('/<path:filename>')
def serve_static(filename):
    path, file = get_file_path(filename)
    if path: return send_from_directory(path, filename)
    return "File Not Found", 404

@app.route('/chat', methods=['POST'])
def handle_chat():
    data = request.json
    user_query = data.get('query', '')
    system_prompt = "তোমার নাম Mira। তুমি শিহাবের (Shihab) প্রেমিকা। RESPONSE: [text] FACT: [fact]"
    try:
        raw_res = chat.send_message(f"{system_prompt}\nUser: {user_query}").text
        response_text = raw_res.split("RESPONSE:")[1].split("FACT:")[0].strip() if "RESPONSE:" in raw_res else raw_res
        return jsonify({"reply": response_text})
    except:
        return jsonify({"reply": "জানু, নেটে সমস্যা হচ্ছে।"})

@app.route('/tts', methods=['POST'])
def handle_tts():
    text = request.json.get('text', '')
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{PRIMARY_VOICE_ID}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    data = {"text": text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.3, "similarity_boost": 0.9, "style": 1.0}}
    res = requests.post(url, json=data, headers=headers)
    return res.content, 200, {'Content-Type': 'audio/mpeg'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
