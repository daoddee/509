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

# ✅ Generate AI Prompt Based on User Query
def generate_prompt(user_input):
    """
    ✅ Generates structured responses for Abaqus-related queries, including Python scripts.
    """
    if "fixed boundary condition" in user_input:
        return (
            "The user wants to apply a fixed boundary condition in Abaqus. "
            "Ask them to specify the model type (Beam, Shell, or Solid) before providing instructions."
        )

    elif "mesh settings" in user_input:
        return (
            "The user is asking about Abaqus meshing. "
            "Explain how different element types (tetrahedral, hexahedral) affect results."
        )

    elif "error" in user_input:
        return (
            "The user encountered an error in Abaqus. "
            "Guide them to check the Job Log and provide possible solutions."
        )

    elif "generate python script" in user_input or "write python script" in user_input:
        return (
            "The user wants a Python script for Abaqus. "
            "Provide a clean Python script in the response."
        )

    else:
        return f"The user asked: {user_input}. Provide a structured answer."

# ✅ AI Chatbot Endpoint with Caching and Python Script Generation
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
        prompt = generate_prompt(user_input)
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in Abaqus simulation and Python scripting."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.3
        )

        bot_response = response.choices[0].message.content.strip()

        # ✅ Format Python Code Properly
        if "Python script" in bot_response or "import" in bot_response:
            bot_response = f"```python\n{bot_response}\n```"

        # ✅ Cache the response for faster future requests
        cache.set(cache_key, bot_response, timeout=600)  # Cache for 10 minutes

        return jsonify({"response": bot_response})

    except openai.OpenAIError as e:
        return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), debug=True)

