from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, abort
import requests, os, base64
import time
import random
import hashlib
from datetime import datetime
from flask_caching import Cache
import magic  # pip install python-magic
from PIL import Image
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("PLANT_ID_API_KEY")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
EXPIRY_SECONDS = 300 if DEMO_MODE else 86400

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-key-change-in-production")
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["CACHE_TYPE"] = "SimpleCache"
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

# Initialize Flask-Caching
cache = Cache(app)

# Create upload directory if it doesn't exist
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        # Limits uploads to 10
        uploads = session.get("upload_count", 0)
        if uploads >= 10:
            flash("Upload limit reached (10 per session). Clear history to continue.", "error")
            return redirect(url_for("index"))
        
        if not DEMO_MODE and not API_KEY:
            flash("Plant identification service is temporarily unavailable", "error")
            return redirect(url_for("index"))

        # file checks
        if "file" not in request.files:
            flash("No file was selected!", "error")
            return redirect(url_for("index"))
        
        # file checks
        file = request.files["file"]
        if file.filename == "":
            flash("Please choose a file!", "error") 
            return redirect(url_for("index"))

        # file checks
        if not allowed_file(file.filename):
            flash("Invalid file type! Please upload an image.")
            return redirect(url_for("index"))
        
        # name file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_filename = secure_filename(file.filename)
        filename = f"{timestamp}_{original_filename}"

        # save image, after safety checks
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        try:
            file.save(image_path)
            if not image_safety_check(image_path):
                os.remove(image_path)
                flash("File failed security check. Please try a different image.", "error")
                return redirect(url_for("index"))
        except Exception as e:
            flash("Error processing file. Please try again.", "error")
            return redirect(url_for("index"))
        
        image_hash = get_image_hash(image_path)
        result = get_cached_result(image_hash)

        if not result:
            # decode to base64 for API format
            with open(image_path, "rb") as img_file:
                img_base64 = [base64.b64encode(img_file.read()).decode("ascii")]

            # fake api
            if DEMO_MODE:
                fake_result = get_fake_plant_response(filename)
                result = fake_result 
            else:
                # api code
                url="https://plant.id/api/v3/identification"
                params = {
                    "details": "url,common_names,description,treatment,edible_parts,best_watering,best_light_condition,best_soil_type"
                }
                headers = {
                    "Api-Key": API_KEY
                }
                json_data= {
                    "images": img_base64
                }
                response = requests.post(url,params=params,headers=headers, json=json_data, timeout=30)
                if response.status_code not in [200,201]:
                    flash(f"Identification failed. Please try again later. (Error: {response.status_code})", "error")
                    return redirect(url_for("index"))

                result = response.json()
                save_to_cache(image_hash, result)

        session["upload_count"] = uploads + 1
        dictResult = json_to_dict(result)
        results_history = session.get("results_history", {})

        # if its a plant and was not called from cache previously, save to history to be added to image gallery
        if dictResult["is_plant"]:
            results_history[filename] = shorten(dictResult)
            session["results_history"] = results_history

        return redirect(url_for("result", filename=filename))
    except requests.Timeout:
        flash("Request timed out. Please try again.", "error")
        return redirect(url_for("index"))
    except Exception as e:
        flash("Uh Oh, something went wrong.")
        return redirect(url_for("index"))

@app.route("/result/<filename>")
def result(filename):
    results_history = session.get("results_history", {})
    dictResult = results_history.get(filename)
    
    # if no result returned from filename, the result is not a plant
    if not dictResult:
        dictResult = {"is_plant": False}

    return render_template("result.html", filename=filename, result=dictResult)

@app.route("/images")
def images():
    results_history = session.get("results_history", {})

    # Convert to list of dicts for template
    # The reason for this is because my images.html image loading was based on an old dictionary format and
    # I'm too lazy to change it
    history = [{"filename": fn, "result": res} for fn, res in results_history.items()]
    return render_template("images.html", history=history)

@app.route("/image/<filename>")
def load_image(filename):
    # validate filename format
    if not filename or ".." in filename or "/" in filename:
        abort(404)
    
    # check if file exists and is in session history (access control)
    results_history = session.get("results_history", {})
    if filename not in results_history:
        abort(404)  # User can only access their own uploaded images
    
    # ensure it's an image file
    if not allowed_file(filename):
        abort(404)
    
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    
    if not os.path.exists(file_path):
        abort(404)
    
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/clear_history")
def clear_history():
    session.pop("results_history", None)
    session.pop("upload_count", None)
    flash("History cleared successfully!","info")
    return redirect(url_for("index"))

@app.before_request
def cleanup():
    results_history = session.get("results_history", {})
    session["results_history"] = remove_old_images(results_history)

@app.errorhandler(500)
def internal_error(error):
    flash("Something went wrong on our end. Please try again.", "error")
    return redirect(url_for("index"))

@app.errorhandler(404)
def not_found(error):
    flash("Page not found.", "error") 
    return redirect(url_for("index"))

# converts JSON to formatted python dict
def json_to_dict(result):
    suggestions = result.get("result",{}).get("classification",{}).get("suggestions",[])
    dictResult = {
        "name": "Plant is unknown",
        "probability": 0,
        "url": None,
        "edible_parts": None,
        "description": None,
        "common_names": None,
        "is_plant": None,
        "uploaded_at": time.time()
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
    """Generate fake API responses for testing without hitting the real API."""
    # MADE WITH AI
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

def get_image_hash(file_path):
    # credit to https://stackoverflow.com/questions/22058048/hashing-a-file-in-python

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        while True:
            data = f.read(65536) # arbitrary number to reduce RAM usage
            if not data:
                break
            sha256.update(data)

    return sha256.hexdigest()

def get_cached_result(image_hash):
    return cache.get(image_hash)

def save_to_cache(image_hash, result):
    cache.set(image_hash, result, timeout=EXPIRY_SECONDS)

def image_safety_check(file_path):
    try:
        mime_type = magic.from_file(file_path, mime=True)
        allowed_img_types = ["image/jpeg","image/png","image/gif","image/webp"]
        if mime_type not in allowed_img_types:
            return False
        
        with Image.open(file_path) as img:
            img.verify()
        
        return True
    except Exception as e:
        return False
    
def allowed_file(filename):
    if "." not in filename or not filename:
        return False
    
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    DISALLOWED_EXTENSIONS = {"php", "exe", "bat", "sh", "py", "js", "html", "htm"}

    extension = filename.rsplit(".", 1)[1].lower()   

    if extension not in ALLOWED_EXTENSIONS or extension in DISALLOWED_EXTENSIONS:
        return False

    if any(char in filename for char in ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]):
        return False
    
    return True

def remove_old_images(results_history):
    now = time.time()
    valid_results_history = {}
    for filename, history in results_history.items():
        if now - history.get("uploaded_at") < EXPIRY_SECONDS:
            valid_results_history[filename] = history
        else:
            file_path = os.path.join(app.config["UPLOAD_FOLDER"],filename)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except OSError as e:
                print("Failed to remove file")
                pass

    return valid_results_history

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))