from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests, os, base64
import time
import random
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("PLANT_ID_API_KEY")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # file checks
    if 'file' not in request.files:
        flash('No file was selected!', 'error')
        return redirect(url_for('index'))
    
    # file checks
    file = request.files['file']
    if file.filename == '':
        flash('Please choose a file!') 
        return redirect(url_for('index'))

    # file checks
    if not allowed_file(file.filename):
        flash('Invalid file type! Please upload an image.')
        return redirect(url_for('index'))
    
    # name file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_filename = file.filename
    filename = f"{timestamp}_{original_filename}"

    # save to uploads
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    # decode to base64 for API format
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    with open(image_path, "rb") as img_file:
        img_base64 = [base64.b64encode(img_file.read()).decode("ascii")]
    
    print("🧪 USING FAKE API FOR TESTING")
    fake_result = get_fake_plant_response(filename)
    result = fake_result

    # API CODE - CURRENTLY TESTING NOT USING!
    """ url="https://plant.id/api/v3/identification"
    params = {
        'details': 'url,common_names,description,treatment,edible_parts,best_watering,best_light_condition,best_soil_type'
    }
    headers = {
        "Api-Key": API_KEY
    }
    json= {
        'images':img_base64
    }
    response = requests.post(url,params=params,headers=headers, json=json)

    result = response.json() """

        
    dictResult = jsonToDict(result)
    results_history = session.get('results_history', {})

    if dictResult["is_plant"]:
        results_history[filename] = shorten(dictResult)
        session['results_history'] = results_history

    return redirect(url_for('result', filename=filename))

@app.route('/result/<filename>')
def result(filename):
    results_history = session.get('results_history', {})
    dictResult = results_history.get(filename)
    
    # save result to session history
    if not dictResult:
        dictResult = {"is_plant": False}

    return render_template('result.html', filename=filename, result=dictResult)

@app.route('/images')
def images():
    results_history = session.get('results_history', {})
    # Convert to list of dicts for template
    history = [{"filename": fn, "result": res} for fn, res in results_history.items()]
    return render_template('images.html', history=history)

@app.route("/clear_history")
def clear_history():
    session.pop('results_history', None)
    return redirect(url_for('index'))

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# converts JSON to formatted python dict
def jsonToDict(result):
    suggestions = result.get('result',{}).get('classification',{}).get('suggestions',[])
    dictResult = {
        "name": "Plant is unknown",
        "probability": 0,
        "url": None,
        "edible_parts": [],
        "description": None,
        "common_names": [],
        "is_plant": None
    }

    # plant check
    is_plant = result.get("result",{}).get("is_plant",{})
    dictResult["is_plant"] = is_plant["binary"]

    if suggestions:
        likely_plant = suggestions[0]  
        dictResult["name"] = likely_plant.get("name","Plant is unknown")
        dictResult["probability"] = likely_plant.get("probability",0)

        plant_details = likely_plant.get("details",{})
        if plant_details:
            dictResult["url"] = plant_details.get("url",None)
            dictResult["edible_parts"] = plant_details.get("edible_parts", None)
            description = plant_details.get("description",{})
            if description:
                dictResult["description"] = description.get("value", None)            
            common_names = plant_details.get("common_names",None)
            if common_names:
                dictResult["common_names"] = common_names
    return dictResult

def shorten(dictResult, max_length=500):
    session_result = dictResult.copy()
    description = session_result.get("description")
    if description is not None and len(description) > max_length:
        session_result["description"] = description[:max_length] + "... [shortened]"
    return session_result

def get_fake_plant_response(filename):
    """Generate fake API responses for testing without hitting the real API"""
    
    # List of fake plants with realistic data
    fake_plants = [
        {
            "name": "Zamioculcas zamiifolia",
            "common_names": ["Zanzibar gem", "zeezee plant", "ZZ Plant"],
            "probability": 0.99,
            "description": "Zamioculcas is genus of flowering plants in the family Araceae, containing the single species Zamioculcas zamiifolia. It is a tropical perennial plant, native to eastern Africa, from southern Kenya to northeastern South Africa. Common names include Zanzibar gem, ZZ plant, Zuzu plant, aroid palm, eternity plant and emerald palm.",
            "url": "https://en.wikipedia.org/wiki/Zamioculcas",
            "edible_parts": None
        },
        {
            "name": "Taraxacum sect. Taraxacum",
            "common_names": ["Taraxacum", "dandelions"],
            "probability": 0.85,
            "description": "Taraxacum is a large genus of flowering plants in the family Asteraceae, which consists of species commonly known as dandelions. Both species are edible in their entirety.",
            "url": "https://en.wikipedia.org/wiki/Taraxacum",
            "edible_parts": ["leaves", "flowers", "roots"]
        },
        {
            "name": "Rosa rubiginosa",
            "common_names": ["Sweet briar", "eglantine rose"],
            "probability": 0.78,
            "description": "Rosa rubiginosa is a species of rose native to Europe and western Asia. It is a deciduous shrub normally ranging from 1 to 3 metres in height.",
            "url": "https://en.wikipedia.org/wiki/Rosa_rubiginosa",
            "edible_parts": ["hips", "petals"]
        },
        {
            "name": "Aloe vera",
            "common_names": ["Aloe vera", "true aloe", "barbados aloe"],
            "probability": 0.92,
            "description": "Aloe vera is a succulent plant species of the genus Aloe. It is widely distributed and is considered an invasive species in many world regions.",
            "url": "https://en.wikipedia.org/wiki/Aloe_vera",
            "edible_parts": ["gel"]
        }
    ]
    
    # Determine if it should be a plant or not (90% chance it's a plant for testing)
    is_plant = random.random() > 0.1
    
    if not is_plant:
        # Return "not a plant" response
        return {
            "access_token": "fake_token_123",
            "completed": time.time(),
            "created": time.time() - 1,
            "result": {
                "classification": {"suggestions": []},
                "is_plant": {
                    "binary": False,
                    "probability": 0.23,
                    "threshold": 0.5
                }
            },
            "status": "COMPLETED"
        }
    
    # Pick a random plant
    plant = random.choice(fake_plants)
    
    # Create fake response in the same format as your real API
    fake_response = {
        "access_token": "fake_token_123",
        "completed": time.time(),
        "created": time.time() - 1,
        "custom_id": "None",
        "input": {
            "datetime": "2025-08-12T21:43:25.023703+00:00",
            "images": [f"https://plant.id/media/imgs/fake_{filename}.jpg"],
            "latitude": "None",
            "longitude": "None"
        },
        "model_version": "plant_id:5.0.0",
        "result": {
            "classification": {
                "suggestions": [
                    {
                        "details": {
                            "best_light_condition": "This plant thrives in bright, indirect light.",
                            "best_soil_type": "Well-draining soil with good organic content.",
                            "best_watering": "Water when the top inch of soil is dry.",
                            "common_names": plant["common_names"],
                            "description": {
                                "citation": plant["url"],
                                "license_name": "CC BY-SA 3.0",
                                "license_url": "https://creativecommons.org/licenses/by-sa/3.0/",
                                "value": plant["description"]
                            },
                            "edible_parts": plant["edible_parts"],
                            "entity_id": f"fake_{random.randint(100000, 999999)}",
                            "language": "en",
                            "url": plant["url"]
                        },
                        "id": f"fake_{random.randint(100000, 999999)}",
                        "name": plant["name"],
                        "probability": plant["probability"]
                    }
                ]
            },
            "is_plant": {
                "binary": True,
                "probability": 0.95 + random.random() * 0.04,  # Between 0.95-0.99
                "threshold": 0.5
            }
        },
        "sla_compliant_client": True,
        "sla_compliant_system": True,
        "status": "COMPLETED"
    }
    
    return fake_response

if __name__ == '__main__':
    app.run(debug=True)