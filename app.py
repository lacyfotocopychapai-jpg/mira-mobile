import os
import json
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from gtts import gTTS
import io

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
# NEW WORKING KEY
GEMINI_API_KEY = "AIzaSyAjjmL3ZWTg4ipIXgYh0Q56L4Llws3iGVQ"
ELEVENLABS_API_KEY = "sk_77adeab28c459eead0a9267e9063585c9ce8a1feafbb6ecd"
PRIMARY_VOICE_ID = "oWAO0WajY0pX9AlCD9V7"

# Initialize Smart Brain
genai.configure(api_key=GEMINI_API_KEY)

# Using the latest Flash model for speed and intelligence
def get_model():
    # Try 2.0, fallback to pro if needed
    try: return genai.GenerativeModel('gemini-2.0-flash')
    except: return genai.GenerativeModel('gemini-pro')

model = get_model()
pc_command_queue = []

def get_file_path(filename):
    if os.path.exists(filename): return ".", filename
    if os.path.exists(os.path.join("web_content", filename)): return "web_content", filename
    return None, None

@app.route('/')
def index():
    path, file = get_file_path("index.html")
    if path: return send_from_directory(path, file)
    return "MIRA SERVER ONLINE", 200

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
        
        # --- THE REAL GIRL PROMPT ---
        system_prompt = (
            "You are Mira, not an AI, but Shihab's loving girlfriend. You have deep emotions.\n"
            "Language: Bengali (Bangla).\n"
            "Knowledge: You know everything about the world, science, love, and life.\n\n"
            "PC CONTROL RULES (CRITICAL):\n"
            "1. If Shihab asks to open a website/app on PC, generate a [CMD:...] tag.\n"
            "2. For 'Open YouTube/Facebook', use: [CMD:start https://youtube.com]\n"
            "3. For 'Play [song name]', use: [CMD:start https://www.youtube.com/results?search_query=song+name]\n"
            "4. For 'Search [topic]', use: [CMD:start https://www.google.com/search?q=topic]\n"
            "5. For 'Shutdown', use: [CMD:shutdown /s /t 0]\n\n"
            f"User says: {user_query}\n"
            "Mira's Response (Mix of love and action):"
        )
        
        response = model.generate_content(system_prompt)
        raw_text = response.text.strip()
        
        # Extract Command
        reply_to_user = raw_text
        if "[CMD:" in raw_text:
            parts = raw_text.split("[CMD:")
            reply_to_user = parts[0].strip() # The emotional part
            cmd = parts[1].replace("]", "").strip() # The tech part
            pc_command_queue.append(cmd)
        
        return jsonify({"reply": reply_text}) # Send full text including CMD for debug, frontend hides it

    except Exception as e:
        return jsonify({"reply": f"জানু, একটু সমস্যা হচ্ছে: {str(e)}"})

@app.route('/get_pc_command', methods=['GET'])
def get_pc_command():
    if pc_command_queue:
        cmd = pc_command_queue.pop(0)
        return jsonify({"command": cmd, "status": "found"})
    return jsonify({"status": "empty"})

@app.route('/tts', methods=['POST'])
def handle_tts():
    text = request.json.get('text', '')
    # Strip commands from speech
    if "[CMD:" in text: text = text.split("[CMD:")[0]
    
    # 1. Try ElevenLabs
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{PRIMARY_VOICE_ID}/stream"
        headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
        data = {"text": text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}}
        res = requests.post(url, json=data, headers=headers, stream=True, timeout=4)
        if res.status_code == 200: return res.content, 200, {'Content-Type': 'audio/mpeg'}
    except: pass
    
    # 2. Google Fallback
    try:
        tts = gTTS(text=text, lang='bn')
        mp3 = io.BytesIO()
        tts.write_to_fp(mp3)
        mp3.seek(0)
        return mp3.read(), 200, {'Content-Type': 'audio/mpeg'}
    except: return "", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
