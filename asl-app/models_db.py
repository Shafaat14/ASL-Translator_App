from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import os

# Create a new base for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the base class
db = SQLAlchemy(model_class=Base)

# Gesture model
class Gesture(db.Model):
    """Model for ASL gestures and their definitions"""
    __tablename__ = 'gestures'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), nullable=False)  # e.g., 'A', 'B', etc.
    description = db.Column(db.String(255))  # Description of the gesture
    difficulty_level = db.Column(db.Integer, default=1)  # 1-5 difficulty level
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    recognition_sessions = db.relationship('RecognitionSession', back_populates='gesture')
    
    def __repr__(self):
        return f'<Gesture {self.name}>'

# User model
class User(db.Model):
    """Model for application users"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sessions = db.relationship('RecognitionSession', back_populates='user')
    
    def __repr__(self):
        return f'<User {self.username}>'

# Recognition Session model
class RecognitionSession(db.Model):
    """Model for tracking sign language recognition sessions"""
    __tablename__ = 'recognition_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    gesture_id = db.Column(db.Integer, db.ForeignKey('gestures.id'), nullable=False)
    success = db.Column(db.Boolean, default=False)  # Whether the gesture was correctly recognized
    confidence = db.Column(db.Float)  # Recognition confidence score
    duration_ms = db.Column(db.Integer)  # How long it took to recognize
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='sessions')
    gesture = db.relationship('Gesture', back_populates='recognition_sessions')
    
    def __repr__(self):
        return f'<RecognitionSession {self.id} - Gesture {self.gesture_id}>'

# Practice Progress model
class PracticeProgress(db.Model):
    """Model for tracking a user's practice progress with specific gestures"""
    __tablename__ = 'practice_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    gesture_id = db.Column(db.Integer, db.ForeignKey('gestures.id'), nullable=False)
    proficiency_level = db.Column(db.Integer, default=0)  # 0-100 proficiency
    times_practiced = db.Column(db.Integer, default=0)
    last_practiced = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('progress', lazy=True))
    gesture = db.relationship('Gesture', backref=db.backref('practice_records', lazy=True))
    
    # Composite unique constraint
    __table_args__ = (
        db.UniqueConstraint('user_id', 'gesture_id', name='uix_user_gesture'),
    )
    
    def __repr__(self):
        return f'<PracticeProgress User:{self.user_id} Gesture:{self.gesture_id} Level:{self.proficiency_level}>'

# Helper function to initialize the database with default gestures
def initialize_default_gestures():
    """Initialize the database with default ASL gestures if they don't exist"""
    default_gestures = [
        {'name': 'A', 'description': 'Letter A - Fist with thumb pointing up', 'difficulty_level': 1},
        {'name': 'B', 'description': 'Letter B - All fingers extended and together', 'difficulty_level': 1},
        {'name': 'C', 'description': 'Letter C - Fingers together curved in C shape', 'difficulty_level': 2},
        {'name': 'D', 'description': 'Letter D - Index finger pointing up, others closed', 'difficulty_level': 2},
        {'name': 'E', 'description': 'Letter E - All fingers curled, palm facing out', 'difficulty_level': 1},
        {'name': 'F', 'description': 'Letter F - Index finger and thumb touch, other fingers extended', 'difficulty_level': 3},
        {'name': 'G', 'description': 'Letter G - Index pointing, thumb extended', 'difficulty_level': 2},
        {'name': 'H', 'description': 'Letter H - Index and middle finger extended together', 'difficulty_level': 2},
        {'name': 'I', 'description': 'Letter I - Pinky finger extended, others closed', 'difficulty_level': 1},
        {'name': 'J', 'description': 'Letter J - Pinky extended with J motion', 'difficulty_level': 3},
        {'name': 'K', 'description': 'Letter K - Index and middle finger in V, thumb between', 'difficulty_level': 3},
        {'name': 'L', 'description': 'Letter L - Index finger and thumb in L shape', 'difficulty_level': 1},
        {'name': 'M', 'description': 'Letter M - Thumb tucked between folded fingers', 'difficulty_level': 2},
        {'name': 'N', 'description': 'Letter N - Thumb tucked under index and middle fingers', 'difficulty_level': 2},
        {'name': 'O', 'description': 'Letter O - Fingertips and thumb form circle', 'difficulty_level': 1},
        {'name': 'P', 'description': 'Letter P - Index pointing down, thumb to side', 'difficulty_level': 3},
        {'name': 'Q', 'description': 'Letter Q - Finger pointing down, thumb and pinky out', 'difficulty_level': 3},
        {'name': 'R', 'description': 'Letter R - Crossed index and middle fingers', 'difficulty_level': 3},
        {'name': 'S', 'description': 'Letter S - Fist with thumb over fingers', 'difficulty_level': 2},
        {'name': 'T', 'description': 'Letter T - Thumb between index and middle finger', 'difficulty_level': 2},
        {'name': 'U', 'description': 'Letter U - Index and middle finger extended together', 'difficulty_level': 2},
        {'name': 'V', 'description': 'Letter V - Index and middle finger in V shape', 'difficulty_level': 1},
        {'name': 'W', 'description': 'Letter W - Index, middle, and ring fingers extended', 'difficulty_level': 2},
        {'name': 'X', 'description': 'Letter X - Index finger bent at middle joint', 'difficulty_level': 3},
        {'name': 'Y', 'description': 'Letter Y - Thumb and pinky extended, others closed', 'difficulty_level': 2},
        {'name': 'Z', 'description': 'Letter Z - Index finger traces Z shape', 'difficulty_level': 4},
    ]
    
    for gesture_data in default_gestures:
        # Check if gesture already exists
        gesture = Gesture.query.filter_by(name=gesture_data['name']).first()
        if not gesture:
            # Create new gesture
            gesture = Gesture(
                name=gesture_data['name'],
                description=gesture_data['description'],
                difficulty_level=gesture_data['difficulty_level']
            )
            db.session.add(gesture)
    
    db.session.commit()