from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests, os, base64
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
    
    url="https://plant.id/api/v3/identification"
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

    result = response.json()
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

def shorten(dictResult, max_length=300):
    session_result = dictResult.copy()
    description = session_result.get("description")
    if description is not None and len(description) > max_length:
        session_result["description"] = description[:max_length] + "... [shortened]"
    return session_result

if __name__ == '__main__':
    app.run(debug=True)