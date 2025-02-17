import os
import openai
import hashlib
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_caching import Cache

# ✅ Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app)

# ✅ Caching Configuration
app.config["CACHE_TYPE"] = "simple"
app.cache = Cache(app)

# ✅ Load OpenAI API Key from Environment Variable
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logging.error("⚠️ OpenAI API key is missing! Set it in Render Environment Variables.")
openai.api_key = api_key

def generate_cache_key(prompt):
    """Generate a unique cache key for storing responses"""
    return hashlib.md5(prompt.encode()).hexdigest()

def fetch_ai_response(prompt, cache_key=None):
    """Fetch a response from OpenAI, using caching for efficiency"""
    if cache_key and app.cache.get(cache_key):
        return app.cache.get(cache_key)

    try:
        client = openai.OpenAI(api_key=openai.api_key)  # ✅ Fix API Key Usage
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an Abaqus expert assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.3
        )

        ai_response = response.choices[0].message.content.strip()
        if cache_key:
            app.cache.set(cache_key, ai_response, timeout=600)  # Cache for 10 minutes

        return ai_response

    except openai.AuthenticationError:
        return "⚠️ Invalid OpenAI API key. Please update your Render environment variables."
    except Exception as e:
        logging.error(f"❌ OpenAI Request Failed: {e}")
        return f"❌ Server error: {str(e)}"

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat requests and provide intelligent responses"""
    data = request.get_json()
    user_input = data.get("message", "").strip()

    if not user_input:
        return jsonify({"error": "⚠️ No input provided"}), 400

    # ✅ Handle structured responses
    if "fixed boundary condition" in user_input.lower():
        response = fetch_ai_response(
            "Explain where to place a fixed boundary condition in Abaqus. Ask the user for model details first.",
            cache_key="fixed_boundary_condition"
        )
    elif "start project plan" in user_input.lower():
        response = fetch_ai_response(
            "The user is designing a structural model. Create a step-by-step plan to guide them through the process.",
            cache_key="project_plan"
        )
    else:
        response = fetch_ai_response(user_input, cache_key=generate_cache_key(user_input))

    return jsonify({"response": response})

if __name__ == '__main__':
    logging.info("🚀 Starting Flask server on Render...")
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), debug=True)

