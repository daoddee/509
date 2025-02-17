kimport os
import openai
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_caching import Cache

# ✅ Flask app setup
app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# ✅ Enable caching for better performance
app.config["CACHE_TYPE"] = "simple"
app.config["CACHE_DEFAULT_TIMEOUT"] = 300  # Cache results for 5 minutes
cache = Cache(app)

# ✅ Get OpenAI API key from environment variables (important for Render)
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ AI Response Fetching with caching
@cache.memoize(timeout=300)
def fetch_ai_response(prompt):
    """
    Fetches AI response. Uses cache if available for faster performance.
    """
    try:
        client = openai.OpenAI(api_key=openai.api_key)  # Ensure API key is used

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an Abaqus expert."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.3
        )

        return response.choices[0].message.content.strip()

    except openai.OpenAIError as e:
        return f"⚠️ OpenAI API Error: {str(e)}"
    except Exception as e:
        return f"⚠️ Server Error: {str(e)}"


# ✅ Main chatbot route
@app.route("/chat", methods=["POST"])
def chat():
    """
    Handles chat requests, provides optimized answers for Abaqus-related questions.
    """
    data = request.get_json()
    user_input = data.get("message", "").strip()

    if not user_input:
        return jsonify({"error": "⚠️ No input provided"}), 400

    # ✅ Smart Handling of Abaqus-related Queries
    if "fixed boundary" in user_input.lower():
        response = "To place a fixed boundary in Abaqus: \n1️⃣ Open **Model** ➝ **Assembly** ➝ **Step** \n2️⃣ Navigate to **Load Module** \n3️⃣ Choose **Fixed Support** and select your region. \n\nWould you like a step-by-step guide?"
    elif "meshing" in user_input.lower():
        response = "To mesh your model in Abaqus: \n1️⃣ Go to **Mesh Module** ➝ **Seed Part** \n2️⃣ Adjust global element size \n3️⃣ Use **Mesh Controls** to refine meshing. \n\nDo you need further mesh refinement options?"
    elif "start project plan" in user_input.lower():
        response = fetch_ai_response("The user is designing an Abaqus model. Provide a structured step-by-step project plan.")
    else:
        response = fetch_ai_response(user_input)  # General AI response

    return jsonify({"response": response})


# ✅ Ensure Render Works with Correct Port
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render uses PORT variable
    app.run(host="0.0.0.0", port=port, debug=True)

