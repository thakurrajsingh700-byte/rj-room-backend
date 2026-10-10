import os
import hmac
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from groq import Groq

load_dotenv()
app = Flask(__name__)
API_KEY = os.environ.get("GROQ_API_KEY", "")
APP_TOKEN = os.environ.get("APP_ACCESS_TOKEN", "")
MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
client = Groq(api_key=API_KEY) if API_KEY else None

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "online", "service": "RJRoomControl AI"})

@app.route("/chat", methods=["POST"])
def chat():
    if not APP_TOKEN:
        return jsonify({"error": "Server security is not configured"}), 503
    supplied_token = request.headers.get("X-App-Token", "")
    if not hmac.compare_digest(supplied_token, APP_TOKEN):
        return jsonify({"error": "Unauthorized"}), 401
    if client is None:
        return jsonify({"error": "AI service is not configured"}), 503
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")
    if not isinstance(message, str) or not message.strip():
        return jsonify({"error": "Please provide a message"}), 400
    if len(message) > 2000:
        return jsonify({"error": "Message is too long"}), 400
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are RJ Assistant. Reply helpfully in Hindi or Hinglish, matching the user's language. You may explain room controls, but never claim you actually switched a device. Do not issue electrical commands or operate hardware."},
                {"role": "user", "content": message},
            ],
            max_completion_tokens=500,
        )
        return jsonify({"reply": response.choices[0].message.content or ""})
    except Exception:
        app.logger.exception("Groq request failed")
        return jsonify({"error": "AI request failed"}), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
