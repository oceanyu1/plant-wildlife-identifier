from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    # Get recently uploaded images from session
    user_uploads = session.get('user_uploads', [])
    return render_template('index.html', user_uploads=user_uploads)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file was selected!', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('Please choose a file!') 
        return redirect(url_for('index'))

    if not allowed_file(file.filename):
        flash('Invalid file type! Please upload an image.')
        return redirect(url_for('index'))
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_filename = file.filename
    filename = f"{timestamp}_{original_filename}"

    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    user_uploads = session.get('user_uploads', [])
    user_uploads.append(filename)
    session['user_uploads'] = user_uploads

    return f"File {filename} uploaded"

@app.route('/result/<filename>')
def result(filename):
    return render_template('result.html', filename=filename)

@app.route('/images')
def images():
    user_uploads = session.get('user_uploads', [])
    return render_template('images.html', user_uploads=user_uploads)

@app.route("/clear_history")
def clear_history():
    session.pop('user_uploads', None)
    return redirect(url_for("index"))

def allowed_file(filename):
    """Check if file is an allowed image type"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    app.run(debug=True)