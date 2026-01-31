import os
import json
import requests
import io
import google.generativeai as genai
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from gtts import gTTS

app = Flask(__name__)
CORS(app)

# --- Configuration ---
GEMINI_API_KEY = "AIzaSyDALevog6Y6bJRbYlygpZx_ORGkE2L7Wos"
ELEVENLABS_API_KEY = "sk_77adeab28c459eead0a9267e9063585c9ce8a1feafbb6ecd"
PRIMARY_VOICE_ID = "oWAO0WajY0pX9AlCD9V7"

# Initialize AI Brain
genai.configure(api_key=GEMINI_API_KEY)

# Try to find a working model dynamically
def get_working_model():
    try:
        # Priority list
        candidates = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro', 'gemini-1.0-pro']
        for m in candidates:
            return genai.GenerativeModel(m)
    except:
        return genai.GenerativeModel('gemini-pro')

model = get_working_model()

def get_file_path(filename):
    if os.path.exists(filename): return ".", filename
    if os.path.exists(os.path.join("web_content", filename)): return "web_content", filename
    return None, None

@app.route('/')
def index():
    path, file = get_file_path("index.html")
    if path: return send_from_directory(path, file)
    return "<h1>Mira Error: index.html not found!</h1>", 404

@app.route('/<path:filename>')
def serve_static(filename):
    path, file = get_file_path(filename)
    if path: return send_from_directory(path, filename)
    return "Not Found", 404

@app.route('/chat', methods=['POST'])
def handle_chat():
    try:
        data = request.json
        user_query = data.get('query', '')
        
        system_prompt = (
            "You are Mira, Shihab's girlfriend. Respond in Bengali. Be emotional and loving.\n"
            f"User: {user_query}\n"
            "Response:"
        )
        
        # Safe generation with model fallback info
        try:
            response = model.generate_content(system_prompt)
            text = response.text.replace("Response:", "").strip()
            return jsonify({"reply": text})
        except Exception as gen_error:
            # If generation fails, list available models for debugging
            try:
                available_models = [m.name for m in genai.list_models()]
                return jsonify({"reply": f"Model Error: {str(gen_error)}. Available: {available_models}"})
            except:
                return jsonify({"reply": f"Critical Error: {str(gen_error)}"})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})

@app.route('/tts', methods=['POST'])
def handle_tts():
    text = request.json.get('text', '')
    
    # 1. Try ElevenLabs
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{PRIMARY_VOICE_ID}/stream"
        headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "style": 1.0}
        }
        res = requests.post(url, json=data, headers=headers, stream=True, timeout=5)
        if res.status_code == 200:
            return res.content, 200, {'Content-Type': 'audio/mpeg'}
    except:
        pass

    # 2. Fallback to Google TTS
    try:
        tts = gTTS(text=text, lang='bn')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return mp3_fp.read(), 200, {'Content-Type': 'audio/mpeg'}
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
