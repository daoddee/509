from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import time
import hashlib

app = Flask(__name__)
CORS(app)

# In-memory cache for faster responses
response_cache = {}

# OpenAI API Client Setup
client = openai.OpenAI(api_key="YOUR_OPENAI_API_KEY")  # Replace with your API key

# Session-based user context
user_sessions = {}

def generate_cache_key(prompt):
    """Generates a unique cache key for repeated questions."""
    return hashlib.md5(prompt.encode()).hexdigest()

def fetch_ai_response(prompt, user_id=None):
    """
    Fetches a response from OpenAI with caching and session memory.
    - Uses cache for common questions.
    - Remembers user context.
    """
    cache_key = generate_cache_key(prompt)
    
    # Return cached response if available
    if cache_key in response_cache:
        return response_cache[cache_key]

    # Maintain user conversation history
    if user_id not in user_sessions:
        user_sessions[user_id] = []

    user_sessions[user_id].append({"role": "user", "content": prompt})

    # Limit session history to avoid excessive memory use
    if len(user_sessions[user_id]) > 5:
        user_sessions[user_id] = user_sessions[user_id][-5:]

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an expert Abaqus assistant."},
            *user_sessions[user_id]
        ],
        max_tokens=400,
        temperature=0.3
    )

    ai_response = response.choices[0].message.content.strip()
    
    # Cache the response
    response_cache[cache_key] = ai_response
    
    # Store AI response in user session
    user_sessions[user_id].append({"role": "assistant", "content": ai_response})
    
    return ai_response

@app.route('/chat', methods=['POST'])
def chat():
    """
    Handles chat requests.
    - Provides structured guidance.
    - Keeps track of user session.
    """
    data = request.get_json()
    user_input = data.get("message", "").strip()
    user_id = data.get("user_id", str(time.time()))  # Generates unique session ID

    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    # Special prompts for enhanced assistance
    if "start project plan" in user_input.lower():
        response = fetch_ai_response("Generate a step-by-step Abaqus simulation plan.", user_id)
    elif "current step" in user_input.lower():
        response = fetch_ai_response("Provide the current step of the Abaqus model setup.", user_id)
    elif "fixed boundary condition" in user_input.lower():
        response = fetch_ai_response(
            "Determine the best location for a fixed boundary condition based on model constraints.",
            user_id
        )
    else:
        response = fetch_ai_response(user_input, user_id)

    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True)

