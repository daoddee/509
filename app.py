from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import openai
import os

# Initialize Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)  # Enable CORS

# Simulated caching dictionary
response_cache = {}

# Function to fetch AI response
def fetch_ai_response(prompt):
    """Fetch response from AI model with caching for performance."""
    if prompt in response_cache:
        return response_cache[prompt]  # Return cached response

    # OpenAI API call (Ensure OpenAI API key is set as environment variable)
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an Abaqus expert assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=400,
        temperature=0.3
    )

    # Extract and store response in cache
    ai_response = response.choices[0].message.content.strip()
    response_cache[prompt] = ai_response
    return ai_response

# Homepage Route (Fixes "Not Found" issue)
@app.route('/')
def home():
    return render_template('index.html')  # Serves the frontend HTML page

# Chatbot API Route (Handles POST requests)
@app.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint for AI interaction."""
    data = request.get_json()
    user_input = data.get("message", "").strip()

    if not user_input:
        return jsonify({"error": "No input provided"}), 400

    # Process AI response
    response = fetch_ai_response(user_input)
    return jsonify({"response": response})

# Run the Flask app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Get port dynamically
    app.run(host='0.0.0.0', port=port, debug=True)

