import openai
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

response_cache = {}

def fetch_ai_response(prompt, cache_key=None):
    """
    Fetch a response from the AI. Check the cache first; if not found,
    query the AI model.
    """
    if cache_key and cache_key in response_cache:
        return response_cache[cache_key]

    client = openai.OpenAI(api_key=openai.api_key)  # ✅ Use the new API format

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an Abaqus expert assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=400,
        temperature=0.3
    )

    ai_response = response.choices[0].message.content.strip()  # ✅ FIX INDENTATION

    if cache_key:
        response_cache[cache_key] = ai_response

    return ai_response

@app.route('/chat', methods=['POST'])
def chat():
    """
    Handle chat requests. The bot first determines the user's goal,   
    then provides a structured plan.
    """
    data = request.get_json()
    user_input = data.get("message", "").strip()

    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    if "start project plan" in user_input.lower():
        response = fetch_ai_response("The user is designing a structural model. Develop a step-by-step plan.", cache_key="project_plan")
    elif "current step" in user_input.lower():
        response = fetch_ai_response("Provide the current step of the project and the next immediate action.")
    else:
        response = fetch_ai_response(user_input)

    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True)

