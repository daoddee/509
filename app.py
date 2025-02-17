from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure API Key is Set
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ ERROR: OPENAI_API_KEY is missing from environment variables.")

# Initialize OpenAI Client
client = openai.OpenAI(api_key=api_key)

# Initialize Flask App
app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Test Route (Check if API is Live)
@app.route("/", methods=['GET'])
def home():
    return "✅ Abaqus Chatbot API is running!"

# Chat Route
@app.route('/chat', methods=['POST'])
def chat():
    try:
        # Get user input
        data = request.get_json()
        user_input = data.get("message", "").strip().lower()  # Normalize input

        if not user_input:
            return jsonify({"error": "No message provided"}), 400

        # Get the response style from the request, default to "detailed"
        style = data.get("style", "detailed")

        # Define system messages based on the selected style
        if style == "simple":
            system_message = "Explain Abaqus and Finite Element Analysis in an easy-to-understand way. Assume the user is new to engineering concepts."
        elif style == "advanced":
            system_message = "You are an Abaqus expert. Provide in-depth technical responses including Abaqus scripting, command syntax, and real-world use cases. Use precise engineering terminology."
        elif style == "concise":
            system_message = "Provide a short, direct, and technical response about Abaqus without unnecessary details."
        else:
            system_message = "You are an expert in Abaqus and Finite Element Analysis (FEA). Provide clear, detailed, and technical responses with references to Abaqus functionalities."

        # Generate response using OpenAI API
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_input}
            ]
        )

        ai_response = response.choices[0].message.content

        return jsonify({"response": ai_response})

    except openai.OpenAIError as e:
        return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# Run Flask App
if __name__ == '__main__':
    app.run(debug=True)

