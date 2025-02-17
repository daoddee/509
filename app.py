from flask import Flask, request, jsonify
from flask_cors import CORS
import openai

app = Flask(__name__)
CORS(app)

response_cache = {}

def fetch_ai_response(prompt, cache_key=None):
    """
    Fetch a response from the AI. Check the cache first; if not found,
    query the AI model.
    """
    if cache_key and cache_key in response_cache:
        return response_cache[cache_key]

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an Abaqus expert assistant that always begins by thoroughly understanding the user's project goals. You create a step-by-step plan to guide the user through their design, ensuring nothing is overlooked."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=400,
        temperature=0.3
    )

    ai_response = response['choices'][0]['message']['content'].strip()

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
        response = fetch_ai_response(
            "The user is designing a structural model. Develop a step-by-step plan to ensure the user doesn’t miss any critical steps and sticks to the plan throughout the project.",
            cache_key="project_plan"
        )
    elif "current step" in user_input.lower():
        response = fetch_ai_response(
            "Provide the current step of the project and the next immediate action the user should take. Include brief guidance if necessary."
        )
    else:
        response = fetch_ai_response(user_input)

    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True)

