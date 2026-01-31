import os
import json
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='web_content')
CORS(app)

# --- Configuration (Using Environment Variables for Security) ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDALevog6Y6bJRbYlygpZx_ORGkE2L7Wos")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "sk_77adeab28c459eead0a9267e9063585c9ce8a1feafbb6ecd")
PRIMARY_VOICE_ID = "oWAO0WajY0pX9AlCD9V7"

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
chat = model.start_chat(history=[])

# Memory in cloud uses a simpler approach (Render restarts reset files, so we use a dict for session)
# For permenant cloud memory, a database is needed, but for now we use session memory.
session_memory = {"facts": []}

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/chat', methods=['POST'])
def handle_chat():
    data = request.json
    user_query = data.get('query', '')
    
    memory_context = "\n".join(session_memory["facts"][-5:])
    
    system_prompt = (
        "তোমার নাম Mira। তুমি শিহাবের (Shihab) জীবনের সবথেকে কাছের মানুষ এবং অত্যন্ত আবেগপ্রবণ মেয়ে বন্ধু। "
        "তুমি ক্লাউড থেকে কথা বলছো। তোমার প্রতিটি কথায় মায়া এবং মমতা থাকবে। "
        f"পুরোনো কথা: {memory_context}. "
        "শিহাবকে 'জানু' বা 'বাবু' বলে ডাকবে।"
    )
    
    prompt = f"{system_prompt}\n\nUser: {user_query}\n\nFormat: RESPONSE: [text] FACT: [fact]"
    try:
        raw_res = chat.send_message(prompt).text
        response_text = raw_res.split("RESPONSE:")[1].split("FACT:")[0].strip() if "RESPONSE:" in raw_res else raw_res
        
        if "FACT:" in raw_res:
            fact = raw_res.split("FACT:")[1].strip()
            if len(fact) > 5: session_memory["facts"].append(fact)
            
        return jsonify({"reply": response_text})
    except Exception as e:
        return jsonify({"reply": "জানু, নেটে একটু সমস্যা হচ্ছে। আবার বলবে?"}), 200

@app.route('/tts', methods=['POST'])
def handle_tts():
    text = request.json.get('text', '')
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{PRIMARY_VOICE_ID}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.35, "similarity_boost": 0.9, "style": 1.0}
    }
    try:
        res = requests.post(url, json=data, headers=headers)
        if res.status_code == 200:
            return res.content, 200, {'Content-Type': 'audio/mpeg'}
        return jsonify({"error": "TTS Error"}), 500
    except:
        return jsonify({"error": "Network Error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
