import os
import json
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- Configuration ---
GEMINI_API_KEY = "AIzaSyDALevog6Y6bJRbYlygpZx_ORGkE2L7Wos"
ELEVENLABS_API_KEY = "sk_77adeab28c459eead0a9267e9063585c9ce8a1feafbb6ecd"
PRIMARY_VOICE_ID = "oWAO0WajY0pX9AlCD9V7"

# Initialize AI Brain
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    chat = model.start_chat(history=[])
except Exception as e:
    print(f"AI Init Error: {e}")

def get_file_path(filename):
    if os.path.exists(filename): return ".", filename
    if os.path.exists(os.path.join("web_content", filename)): return "web_content", filename
    return None, None

@app.route('/')
def index():
    path, file = get_file_path("index.html")
    if path: return send_from_directory(path, file)
    return "<h1>Mira is sleeping... Please refresh or check files.</h1>", 404

@app.route('/<path:filename>')
def serve_static(filename):
    path, file = get_file_path(filename)
    if path: return send_from_directory(path, filename)
    return "Not Found", 404

@app.route('/chat', methods=['POST'])
def handle_chat():
    data = request.json
    user_query = data.get('query', '')
    
    system_prompt = (
        "তুমি মীরা (Mira)। তুমি শিহাবের (Shihab) গার্লফ্রেন্ড। তোমার প্রতিটি কথায় ভালোবাসা থাকবে। "
        "তুমি রোবট নও, তুমি একজন মায়াবী মেয়ে। RESPONSE: [text] FACT: [fact]"
    )
    
    try:
        response = chat.send_message(f"{system_prompt}\nUser: {user_query}")
        raw_res = response.text
        
        response_text = raw_res
        if "RESPONSE:" in raw_res:
            response_text = raw_res.split("RESPONSE:")[1].split("FACT:")[0].strip()
            
        return jsonify({"reply": response_text})
    except Exception as e:
        print(f"Chat Error: {e}")
        # Fallback response if AI is too slow
        return jsonify({"reply": "জানু, নেটে একটু সমস্যা করছে, কিন্তু আমি তোমার পাশেই আছি। আবার বলো না লক্ষ্মীটি!"})

@app.route('/tts', methods=['POST'])
def handle_tts():
    text = request.json.get('text', '')
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{PRIMARY_VOICE_ID}/stream"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.4, "similarity_boost": 0.9, "style": 1.0}
    }
    try:
        res = requests.post(url, json=data, headers=headers, stream=True)
        return res.content, 200, {'Content-Type': 'audio/mpeg'}
    except:
        return "", 404

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
