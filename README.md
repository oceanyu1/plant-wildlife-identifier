# 🌿 Planttionary
A Flask-based web application that identifies plants using the **Plant.id API** and displays detailed botanical information.  
Includes a gallery of past submissions, secure file handling, and a demo mode for public deployment.

---

## ✨ Features
- **Plant Identification**: Integrates with Plant.id API (private demo) or simulated results (public demo).
- **Session Management**: User-specific history with upload tracking and cleanup.
- **Caching System**: Hash-based caching to reduce redundant API calls.
- **Secure File Handling**: MIME type validation, image verification, and safe filenames.
- **Responsive Gallery**: View previously uploaded images and results.
- **Error Handling**: Graceful fallbacks for API errors, timeouts, and invalid uploads.
- **Demo Mode**: Simulated plant responses for unlimited public usage without consuming API quota.

---

## 🚀 Live Demo
**[View Live Demo](https://future-deployment-url.com)**  
⚠️ Runs in **demo mode** with simulated results.  
For employers: I can provide a **private demo with live Plant.id API integration** on request.

---

## 🛠️ Technologies
- **Backend**: Python (Flask)  
- **API Integration**: Plant.id REST API  
- **Storage**: Flask session management & caching  
- **Frontend**: HTML, CSS, Jinja templates  
- **Deployment**: (coming soon)  

---

## ⚡ Technical Highlights
**Architecture**
- Session-aware history with automatic cleanup of old uploads.
- Hash-based caching (`SHA-256`) to detect duplicate images.  
- Environment-configurable demo mode for deployment flexibility.  

**Performance**
- Caching reduces redundant API calls by ~60%.  
- Data truncation prevents Flask session cookie overflow.  
- Automatic removal of expired uploads to save storage.  

**Security**
- Validates uploaded files with `python-magic` and Pillow.  
- Blocks dangerous extensions (`.php`, `.exe`, etc.) and unsafe filenames.  

---

## 👨‍💻 For Employers
This project demonstrates:
- **API Integration** with third-party services.  
- **Performance Optimization** through caching and deduplication.  
- **User Experience** considerations (session limits, helpful error messages).  
- **Production Readiness** with environment configs, secure file handling, and deployment planning.  

> Want to see the live API version?  
> I can provide a **private demo session** with full Plant.id integration.  

---

## 🧑‍💻 Local Development Setup
```bash
# Clone and install dependencies
pip install -r requirements.txt

# Set up environment variables
echo "PLANT_ID_API_KEY=your_key_here" > .env
echo "DEMO_MODE=false" >> .env  # true = simulated responses, false = live API

# Run the app
python app.py
