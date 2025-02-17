
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import openai
from flask_caching import Cache

app = Flask(__name__, static_folder="static")  # Serves HTML from 'static' folder
CORS(app)

# ✅ Configure Caching for Faster Responses
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# ✅ Load API Key from Environment Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ OpenAI API Key is missing. Set OPENAI_API_KEY in environment variables.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ✅ Track User's Abaqus Model Progress
user_sessions = {}

# ✅ Serve HTML File for Frontend
@app.route('/')
def serve_index():
    return send_from_directory("static", "index.html")

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory("static", path)

# ✅ AI Chatbot with Step-by-Step Abaqus Assistance
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_input = data.get("message", "").strip()
    user_id = data.get("user_id", "default_user")  # Track user's session

    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    # ✅ Check if the user has a session, otherwise create one
    if user_id not in user_sessions:
        user_sessions[user_id] = {"step": "start", "model_type": None}

    user_context = user_sessions[user_id]
    cache_key = f"chat_response:{user_input.lower()}"

    # ✅ Return Cached Response if Available
    cached_response = cache.get(cache_key)
    if cached_response:
        return jsonify({"response": cached_response})

    try:
        response_text = ""

        # ✅ Step 1: Ask for Model Type Before Answering Abaqus-Specific Questions
        if user_context["step"] == "start":
            response_text = "What kind of model are you working on? (Beam, Shell, or Solid?)"
            user_sessions[user_id]["step"] = "waiting_for_model_type"

        elif user_context["step"] == "waiting_for_model_type":
            user_sessions[user_id]["model_type"] = user_input.capitalize()
            user_sessions[user_id]["step"] = "ready"
            response_text = f"Got it! You are working on a {user_input.capitalize()} model. What do you need help with next?"

        else:
            # ✅ Normal AI Response for Abaqus Queries
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert Abaqus assistant. Keep answers precise and technical."},
                    {"role": "user", "content": user_input}
                ],
                max_tokens=300,
                temperature=0.3
            )
            response_text = response.choices[0].message.content.strip()

        # ✅ Cache Response for Faster Future Requests
        cache.set(cache_key, response_text, timeout=600)  # Cache for 10 minutes

        return jsonify({"response": response_text})

    except openai.OpenAIError as e:
        return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), debug=True)

