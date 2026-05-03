pip install flask requests flask-cors
    export DEEPSEEK_API_KEY="sk-f894ba5d0c8342db87144a713113a084"
    python yasia_ai_proxy.py

В хабе укажи Proxy URL: http://127.0.0.1:8787/yasia
"""
import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # чтобы хаб мог обращаться с любого источника

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    print("⚠️  Установите переменную окружения DEEPSEEK_API_KEY")
    # Не падаем с ошибкой, даём осознать при первом же запросе

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

@app.route("/", methods=["GET"])
def health():
    return "Yasya AI Proxy Running", 200

@app.route("/yasia", methods=["POST"])
def yasia():
    if not DEEPSEEK_API_KEY:
        return jsonify({"error": "API key not set on server"}), 500

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    # Извлекаем параметры, которые передаёт хаб
    model = data.get("model", "deepseek-chat")
    messages = data.get("messages", [])
    temperature = data.get("temperature", 0.7)
    max_tokens = data.get("max_tokens", 1024)

    if not messages:
        return jsonify({"error": "No messages provided"}), 400

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        # можно добавить stream: False, если не нужна потоковая передача
    }

    try:
        resp = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()  # выбросит ошибку при 4xx/5xx
        result = resp.json()
        # Возвращаем содержимое ответа DeepSeek в удобном виде
        return jsonify(result), 200
    except requests.exceptions.RequestException as e:
        # Пробрасываем ошибку от DeepSeek
        error_msg = str(e)
        if hasattr(e, "response") and e.response is not None:
            error_msg = e.response.text
        return jsonify({"error": f"DeepSeek API error: {error_msg}"}), 502

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8787))
    app.run(host="0.0.0.0", port=port, debug=False)