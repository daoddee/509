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

# ✅ AI Chatbot Endpoint with Caching
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

    # ✅ Decision Making for Abaqus Script Generation
    abaqus_scripts = {
        "fixed boundary condition": """
from abaqus import *
from abaqusConstants import *
from caeModules import *

mdb.models['Model-1'].parts['Part-1'].Set(name='FixedSet', faces=mdb.models['Model-1'].parts['Part-1'].faces.findAt(((0.0, 0.0, 0.0),)))
mdb.models['Model-1'].rootAssembly.Set(name='FixedSet', faces=mdb.models['Model-1'].rootAssembly.instances['Part-1-1'].faces.findAt(((0.0, 0.0, 0.0),)))
mdb.models['Model-1'].boundaryConditions['BC-1'] = mdb.models['Model-1'].StaticStep(name='Step-1', previous='Initial').DisplacementBC(name='BC-1', createStepName='Step-1', region=mdb.models['Model-1'].rootAssembly.sets['FixedSet'], u1=0.0, u2=0.0, u3=0.0, ur1=0.0, ur2=0.0, ur3=0.0, amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='', localCsys=None)
""",
        "apply load": """
from abaqus import *
from abaqusConstants import *
from caeModules import *

mdb.models['Model-1'].rootAssembly.Set(name='LoadSet', faces=mdb.models['Model-1'].rootAssembly.instances['Part-1-1'].faces.findAt(((5.0, 0.0, 0.0),)))
mdb.models['Model-1'].loads['Load-1'] = mdb.models['Model-1'].StaticStep(name='Step-1', previous='Initial').ConcentratedForce(name='Load-1', createStepName='Step-1', region=mdb.models['Model-1'].rootAssembly.sets['LoadSet'], cf1=-100.0, amplitude=UNSET)
""",
    }

    # ✅ Detect if user asks for an Abaqus script
    for key in abaqus_scripts.keys():
        if key in user_input.lower():
            bot_response = f"Here is the Abaqus Python script for {key}:\n```python\n{abaqus_scripts[key]}\n```"
            cache.set(cache_key, bot_response, timeout=600)  # Cache for 10 minutes
            return jsonify({"response": bot_response})

    try:
        # ✅ Request AI Response from OpenAI
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in Abaqus simulation."},
                {"role": "user", "content": user_input}
            ],
            max_tokens=300,
            temperature=0.3
        )

        bot_response = response.choices[0].message.content.strip()

        # ✅ Cache the response for faster future requests
        cache.set(cache_key, bot_response, timeout=600)  # Cache for 10 minutes

        return jsonify({"response": bot_response})

    except openai.OpenAIError as e:
        return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), debug=True)

