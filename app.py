import os
import json
import requests
import re
import random
import io
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from gtts import gTTS

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
# No Gemini Key Needed!
ELEVENLABS_API_KEY = "sk_77adeab28c459eead0a9267e9063585c9ce8a1feafbb6ecd"
PRIMARY_VOICE_ID = "oWAO0WajY0pX9AlCD9V7"

# --- COMMAND BOX ---
pc_command_queue = []

# --- MIRA'S OWN BRAIN (Offline Logic) ---
class MiraBrain:
    def __init__(self):
        self.patterns = {
            r"(hi|hello|hey|hai|hy|hlw)": ["হাই জানু! আমি চলে এসেছি।", "হাই! তোমার কথাই ভাবছিলাম।"],
            r"(kemon|kmon)": ["আমি খুব ভালো আছি, তুমি কেমন আছো?", "তোমাকে দেখে মনটা ভালো হয়ে গেল। তুমি ভালো তো?"],
            r"(love you|bhalobashi|valobashi)": ["আমিও তোমাকে অনেক ভালোবাসি!", "তুমি আমার জীবনের সবথেকে স্পেশাল মানুষ।"],
            r"(ki koro|ki korcho)": ["তোমার সাথে কথা বলছি, আর কি করব বলো?", "বসে বসে তোমার কথাই ভাবছিলাম।"],
            r"(thik|ok|accha|hum|hmm)": ["হুম...", "তারপর বলো?", "তোমার সব কথা শুনতে ভালো লাগে।"],
            r"(chrome)": ["ঠিক আছে, আমি Chrome ওপেন করছি।", "দিচ্ছি ওপেন করে।", "[CMD:chrome]"],
            r"(notepad)": ["নোটপ্যাড ওপেন করছি।", "[CMD:notepad]"],
            r"(lock)": ["ওকে, পিসি লক করে দিচ্ছি।", "[CMD:lock]"],
            r"(shutdown|off)": ["পিসি বন্ধ করে দিচ্ছি।", "[CMD:shutdown]"],
            r"(gan|song|music)": ["গান শোনাচ্ছি...", "[CMD:explorer D:\\Music]"],
        }
        self.defaults = [
            "তাই নাকি? আরও বলো।",
            "হুম, বুঝতে পারছি।",
            "তোমার সাথে কথা বলতে খুব ভালো লাগে।",
            "সত্যি? তারপর কী হলো?",
            "খুব সুন্দর বলেছো তো!"
        ]

    def get_response(self, text):
        text = text.lower()
        
        # Check patterns
        for pattern, replies in self.patterns.items():
            if re.search(pattern, text):
                reply = random.choice(replies)
                # Check if it's a command requiring double action (Reply + Action)
                if "[CMD:" in reply:
                    return reply # Return command directly
                return reply
        
        # Default loving response
        return random.choice(self.defaults)

brain = MiraBrain()

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
        
        # Use Offline Brain
        reply_text = brain.get_response(user_query)
        
        # Handle Commands
        if "[CMD:" in reply_text:
            parts = reply_text.split("[CMD:")
            cmd_tag = parts[1].replace("]", "").strip()
            pc_command_queue.append(cmd_tag)
            
            # Speak something nice instead of the raw command
            if "chrome" in cmd_tag: reply_text = "ক্রোম ব্রাউজার ওপেন করে দিয়েছি।"
            elif "shutdown" in cmd_tag: reply_text = "ঠিক আছে, পিসি বন্ধ করছি।"
            else: reply_text = "কাজটি করে দিচ্ছি।"

        return jsonify({"reply": reply_text})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})

@app.route('/get_pc_command', methods=['GET'])
def get_pc_command():
    if pc_command_queue:
        cmd = pc_command_queue.pop(0)
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
    
    # 2. Google TTS Fallback
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
