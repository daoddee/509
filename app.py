import os
import openai
import hashlib
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_caching import Cache

app = Flask(__name__)
CORS(app)

# ✅ Caching Configuration (Improves Performance)
app.config["CACHE_TYPE"] = "simple"
app.cache = Cache(app)

# ✅ Load OpenAI API Key from Environment Variable
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_cache_key(prompt):
    """Generate a unique cache key for each unique request"""
    return hashlib.md5(prompt.encode()).hexdigest()

def fetch_ai_response(prompt, cache_key=None):
    """Fetch a response from the AI, with caching to improve response time."""
    if cache_key and app.cache.get(cache_key):
        return app.cache.get(cache_key)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an Abaqus expert assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.3
        )

        ai_response = response["choices"][0]["message"]["content"].strip()
        if cache_key:
            app.cache.set(cache_key, ai_response, timeout=600)  # Cache for 10 minutes

        return ai_response

    except openai.error.AuthenticationError:
        return "⚠️ Invalid OpenAI API key. Check your environment variables."
    except Exception as e:
        return f"❌ Server error: {str(e)}"

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat requests intelligently and efficiently."""
    data = request.get_json()
    user_input = data.get("message", "").strip()

    if not user_input:
        return jsonify({"error": "⚠️ No input provided"}), 400

    # ✅ Understand the context of the user's question
    if "fixed boundary condition" in user_input.lower():
        response = fetch_ai_response(
            "Explain where to place a fixed boundary condition in Abaqus. "
            "Ask the user for the model details first to provide a better answer.",
            cache_key="fixed_boundary_condition"
        )

    elif "where is" in user_input.lower():
        response = fetch_ai_response(
            f"Provide the location of the tool requested by the user. Keep it short and simple. "
            f"Then, ask if they need guidance on how to use the tool. Question: {user_input}",
            cache_key=generate_cache_key(user_input)
        )

    elif "start project plan" in user_input.lower():
        response = fetch_ai_response(
            "The user is designing a structural model. Create a detailed step-by-step plan to guide them "
            "throughout the process. Ensure they do not miss any steps.",
            cache_key="project_plan"
        )

    else:
        response = fetch_ai_response(user_input, cache_key=generate_cache_key(user_input))

    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), debug=True)

