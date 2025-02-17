import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import openai
from flask_caching import Cache

app = Flask(__name__, static_folder="static")  # Serves HTML from 'static' folder
CORS(app)

# ✅ Configure Caching (Uses Simple Memory Cache)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# ✅ Load API Key from Environment Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ OpenAI API Key is missing. Set OPENAI_API_KEY in environment variables.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ✅ Serve the HTML File for Frontend
@app.route('/')
def serve_index():
    return send_from_directory("static", "index.html")

# ✅ Serve other static files (CSS, JS, images)
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory("static", path)

# ✅ AI Chatbot Endpoint with Caching
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get("message", "").strip()

    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    cache_key = f"chat_response:{user_input.lower()}"

    # ✅ Check Cache Before Requesting OpenAI
    cached_response = cache.get(cache_key)
    if cached_response:
        print("🟢 Returning cached response!")
        return jsonify({"response": cached_response})

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in Abaqus simulation."},
                {"role": "user", "content": user_input}
            ],
            max_tokens=300,
            temperature=0.3
        )

        bot_response = response.choices[0].message.content.strip()
        
        # ✅ Cache the response for faster future requests
        cache.set(cache_key, bot_response, timeout=600)  # Cache for 10 minutes

        return jsonify({"response": bot_response})

    except openai.OpenAIError as e:
        return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), debug=True)

