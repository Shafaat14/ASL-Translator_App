import os
import logging
import json
import base64
import numpy as np
import cv2
from flask import Flask, render_template, Response, request, jsonify, session
from model import GestureRecognizer
from sign_language_model import SignLanguageRecognizer
from models_db import db, Gesture, User, RecognitionSession, PracticeProgress, initialize_default_gestures
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
# Initialize SQLAlchemy with the app
db.init_app(app)

try:
    # Initialize the gesture recognizer
    gesture_recognizer = GestureRecognizer()
    # Initialize the sign language recognizer
    sign_language_recognizer = SignLanguageRecognizer()
    logger.info("Recognizers initialized successfully")
except Exception as e:
    logger.error(f"Error initializing recognizers: {e}")
    # Fallback to just the gesture recognizer if there's an issue
    gesture_recognizer = GestureRecognizer()

# Create database tables and load initial data
with app.app_context():
    # Create all database tables
    db.create_all()
    # Initialize default gestures
    initialize_default_gestures()
    logger.info("Database initialized successfully")

@app.route('/')
def index():
    """Render the main page"""
    if 'user_id' not in session:
        # Create a temporary guest user if not logged in
        guest_user = User.query.filter_by(username='guest').first()
        if not guest_user:
            guest_user = User(
                username='guest',
                email='guest@example.com'
            )
            db.session.add(guest_user)
            db.session.commit()
            logger.info(f"Created guest user with ID: {guest_user.id}")
        
        # Set the guest user ID in session
        session['user_id'] = guest_user.id
        logger.info(f"Set guest user ID in session: {session['user_id']}")
    
    return render_template('index.html')

@app.route('/process_frame', methods=['POST'])
def process_frame():
    """Process a frame from the webcam and recognize gestures"""
    try:
        # Get the base64 image from the request
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data received'}), 400
        
        # Decode the base64 image
        image_data = data['image'].split(',')[1]
        image_bytes = base64.b64decode(image_data)
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'error': 'Could not decode image'}), 400
        
        # Process the frame using the gesture recognizer
        results = gesture_recognizer.process_frame(frame)
        
        # Process using the sign language recognizer as well
        try:
            if 'sign_language_recognizer' in globals():
                sign_text, confidence = sign_language_recognizer.process_image(frame)
                
                # Add sign language results to the response if detected
                if sign_text and confidence > 0.5:
                    results['sign_language'] = {
                        'text': sign_text,
                        'confidence': float(confidence)
                    }
        except Exception as sign_error:
            logger.warning(f"Error in sign language processing: {sign_error}")
        
        # Return the results
        return jsonify(results)
    
    except Exception as e:
        logger.exception("Error processing frame")
        return jsonify({'error': str(e)}), 500

@app.route('/get_supported_gestures')
def get_supported_gestures():
    """Return the list of supported gestures"""
    try:
        # First try to get gestures from the database
        db_gestures = Gesture.query.all()
        if db_gestures:
            gestures = [
                {
                    'name': gesture.name,
                    'description': gesture.description,
                    'difficulty_level': gesture.difficulty_level
                } for gesture in db_gestures
            ]
            return jsonify({
                'supported_gestures': gestures
            })
        else:
            # Fall back to the gesture recognizer if no database gestures
            return jsonify({
                'supported_gestures': gesture_recognizer.get_supported_gestures()
            })
    except Exception as e:
        logger.error(f"Error retrieving gestures from database: {e}")
        # Fall back to the gesture recognizer
        return jsonify({
            'supported_gestures': gesture_recognizer.get_supported_gestures()
        })
        
@app.route('/save_recognition', methods=['POST'])
def save_recognition():
    """Save a successful gesture recognition to the database"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Get data from request
        gesture_name = data.get('gesture_name')
        confidence = data.get('confidence', 0.0)
        duration_ms = data.get('duration_ms', 0)
        success = data.get('success', True)
        
        # Find the gesture in the database
        gesture = Gesture.query.filter_by(name=gesture_name).first()
        if not gesture:
            return jsonify({'error': f'Gesture {gesture_name} not found'}), 404
            
        # Get user ID from session if logged in
        user_id = session.get('user_id')
        
        # Create a new recognition session
        recognition_session = RecognitionSession(
            user_id=user_id,
            gesture_id=gesture.id,
            success=success,
            confidence=confidence,
            duration_ms=duration_ms
        )
        
        db.session.add(recognition_session)
        
        # Update the user's practice progress if logged in
        if user_id:
            practice_progress = PracticeProgress.query.filter_by(
                user_id=user_id, 
                gesture_id=gesture.id
            ).first()
            
            if practice_progress:
                # Update existing progress
                practice_progress.times_practiced += 1
                practice_progress.last_practiced = datetime.utcnow()
                if success:
                    # Increase proficiency (max 100)
                    practice_progress.proficiency_level = min(100, practice_progress.proficiency_level + 5)
            else:
                # Create new progress record
                practice_progress = PracticeProgress(
                    user_id=user_id,
                    gesture_id=gesture.id,
                    proficiency_level=10 if success else 5,
                    times_practiced=1
                )
                db.session.add(practice_progress)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Recognition saved successfully'
        })
        
    except Exception as e:
        logger.exception("Error saving recognition")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
        
@app.route('/get_user_progress')
def get_user_progress():
    """Get the user's progress with gestures"""
    try:
        # Get user ID from session if logged in
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({
                'error': 'User not logged in',
                'progress': []
            }), 401
            
        # Get the user's progress for all gestures
        progress = PracticeProgress.query.filter_by(user_id=user_id).all()
        
        # Format the progress data
        progress_data = []
        for p in progress:
            gesture = Gesture.query.get(p.gesture_id)
            progress_data.append({
                'gesture_name': gesture.name,
                'gesture_description': gesture.description,
                'proficiency_level': p.proficiency_level,
                'times_practiced': p.times_practiced,
                'last_practiced': p.last_practiced.isoformat()
            })
            
        return jsonify({
            'success': True,
            'progress': progress_data
        })
        
    except Exception as e:
        logger.exception("Error getting user progress")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/update_database')
def update_database():
    """Admin route to update the database with the full ASL alphabet (A-Z)"""
    try:
        # Re-initialize the default gestures to add the new ones
        initialize_default_gestures()
        return jsonify({
            'success': True,
            'message': 'Database updated with full ASL alphabet (A-Z)'
        })
    except Exception as e:
        logger.exception("Error updating database")
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
