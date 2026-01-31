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
GEMINI_API_KEY = "AIzaSyAjjmL3ZWTg4ipIXgYh0Q56L4Llws3iGVQ"
ELEVENLABS_API_KEY = "sk_77adeab28c459eead0a9267e9063585c9ce8a1feafbb6ecd"
PRIMARY_VOICE_ID = "oWAO0WajY0pX9AlCD9V7"

# Initialize AI
genai.configure(api_key=GEMINI_API_KEY)
def get_working_model():
    return genai.GenerativeModel('gemini-2.0-flash')
model = get_working_model()

# --- COMMAND BOX (Shared Memory) ---
# Here we store commands for the PC to fetch
pc_command_queue = []

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
        
        # Smart Instruction for PC Control + Messaging
        system_prompt = (
            "You are Mira, Shihab's girlfriend. Respond in Bengali. Be emotional.\n"
            "Capabilities:\n"
            "1. If user wants to send WhatsApp, add tag: [WA:message]\n"
            "2. If user wants to open App/File on PC, add tag: [CMD:app_name]\n"
            "   Example: 'Open Chrome' -> '[CMD:chrome]'\n"
            "   Example: 'Open Photos' -> '[CMD:explorer d:\\photos]'\n"
            f"User: {user_query}\n"
            "Response:"
        )
        
        try:
            response = model.generate_content(system_prompt)
            raw_text = response.text.replace("Response:", "").strip()
            
            # Extract PC Command
            reply_text = raw_text
            if "[CMD:" in raw_text:
                parts = raw_text.split("[CMD:")
                reply_text = parts[0].strip() # The spoken part
                raw_command = parts[1].split("]")[0].strip() # The command part
                pc_command_queue.append(raw_command) # Add to queue for PC
            
            return jsonify({"reply": reply_text})
            
        except Exception as gen_err:
             # Fallback if model fails
             return jsonify({"reply": f"Model Error: {str(gen_err)}"})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})

# --- Endpoint for PC to check for commands ---
@app.route('/get_pc_command', methods=['GET'])
def get_pc_command():
    if pc_command_queue:
        cmd = pc_command_queue.pop(0) # Get and remove latest command
        return jsonify({"command": cmd, "status": "found"})
    return jsonify({"status": "empty"})

@app.route('/tts', methods=['POST'])
def handle_tts():
    text = request.json.get('text', '')
    # 1. Try ElevenLabs
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{PRIMARY_VOICE_ID}/stream"
        headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
        data = {"text": text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}}
        res = requests.post(url, json=data, headers=headers, stream=True, timeout=5)
        if res.status_code == 200: return res.content, 200, {'Content-Type': 'audio/mpeg'}
    except: pass
    # 2. Back up to Google TTS
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
