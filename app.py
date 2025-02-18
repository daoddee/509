import os
import subprocess
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import openai

app = Flask(__name__)
CORS(app)

# ✅ Load API Key from Environment Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ OpenAI API Key is missing. Set OPENAI_API_KEY in environment variables.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ✅ Function to Generate Abaqus Python Scripts
def generate_abaqus_script(user_request):
    """Uses AI to generate an Abaqus Python script based on user input."""
    prompt = f"Generate a complete Abaqus Python script for: {user_request}"

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an expert in Abaqus scripting."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.3
    )

    script = response.choices[0].message.content.strip()

    script_path = "static/generated_script.py"
    with open(script_path, "w") as file:
        file.write(script)

    return script_path

# ✅ API Endpoint to Generate Script
@app.route('/generate_script', methods=['POST'])
def generate_script():
    data = request.get_json()
    user_request = data.get("description", "a simple Abaqus model")

    script_path = generate_abaqus_script(user_request)
    return jsonify({"message": "✅ Abaqus script generated successfully!", "script_path": script_path})

# ✅ API Endpoint to Download the Script
@app.route('/download_script')
def download_script():
    return send_file("static/generated_script.py", as_attachment=True)

# ✅ API Endpoint to Run Abaqus Script
@app.route('/run_script', methods=['POST'])
def run_script():
    script_path = "static/generated_script.py"

    if not os.path.exists(script_path):
        return jsonify({"error": "⚠️ Script not found. Generate it first."}), 404

    try:
        # 🛠️ Run Abaqus CAE in the background
        abaqus_command = f"abaqus cae noGUI={script_path}"
        process = subprocess.run(abaqus_command, shell=True, capture_output=True, text=True)

        if process.returncode == 0:
            return jsonify({"message": "✅ Abaqus script executed successfully!"})
        else:
            return jsonify({"error": f"Abaqus execution failed: {process.stderr}"}), 500

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# ✅ Run Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), debug=True)

