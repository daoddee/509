from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
from dotenv import load_dotenv
from flask_caching import Cache  # Import caching

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

# Set up caching
cache = Cache(app, config={'CACHE_TYPE': 'simple'})  # Simple in-memory cache


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

        # Generate a cache key based on input and style
        cache_key = f"{style}_{user_input}"

        # Check if response is already cached
        cached_response = cache.get(cache_key)
        if cached_response:
            return jsonify({"response": cached_response, "cached": True})

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

        # Store response in cache for faster future access
        cache.set(cache_key, ai_response, timeout=600)  # Cache for 10 minutes

        return jsonify({"response": ai_response, "cached": False})

    except openai.OpenAIError as e:
        return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True)

