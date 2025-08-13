# 🌿 Planttionary
A Flask-based web application that identifies plants using the Plant.id API and provides detailed botanical information, including a gallery showing past submissions, and...

Features Implemented:

• Plant Identification: Accurate plant recognition via Plant.id API.

• Session Management: User-specific history with optimized cookie storage.

• Caching System: File-based caching to reduce API calls and improve performance.

• Image Processing: Base64 encoding for API compatibility.

• Responsive Gallery: Display of user's uploaded images and results.

• Error Handling: Comprehensive validation and user feedback.

# **Live Demo**
View Live Demo - Running in demo mode with pre-cached results.

Note: The live demo uses cached responses to demonstrate functionality without consuming API quota. For employers, I can provide a private demo with live API calls upon request.

# **Technologies Used:**
Backend: Python (Flask).

API Integration: Plant.id REST API.

Storage: File-based caching, session management.

Frontend: HTML, CSS.

Deployment: coming soon.

# **Technical Highlights:**
**Architecture:**

• Session Optimization: Implemented data truncation to solve Flask's 4KB cookie limit:

pythondef truncate_for_session(dictResult, max_description_length=500):
    # Intelligent truncation preserving essential data

• Caching Strategy: File-based caching system to minimize API calls:

pythondef get_cached_result(image_hash):
    # Hash-based caching for duplicate image detection

**Performance:**

API Call Reduction: Implemented image hash-based caching (reduces redundant calls by ~60%)

Session Size Management: Data truncation prevents cookie overflow issues

Storage Efficiency: Automatic cleanup of old uploads

Error Recovery: Graceful fallbacks for API timeouts/failures

# **For Employers:**
This project demonstrates:
API Integration skills with external services.
Performance Optimization through caching strategies.
User Experience considerations (session management, error handling).
Production Readiness (environment configs, resource management).

Want to see it with live API calls? Contact me for a private demo session where I can show the full functionality with real Plant.id integration.

# **Local Development Setup**
```bash
# Clone and install dependencies
pip install -r requirements.txt

# Set up environment variables
echo "PLANT_ID_API_KEY=your_key_here" > .env
echo "DEMO_MODE=false" >> .env  # Set to true for demo mode

# Run application
python app.py
```

📸 Screenshots
(future screenshots coming)

Built with ❤️ as a portfolio project demonstrating full-stack development skills
