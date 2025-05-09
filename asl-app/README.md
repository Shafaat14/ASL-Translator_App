# ASL Translator Web Application

This is a web-based application that uses computer vision to recognize American Sign Language (ASL) gestures from webcam input and translates them into text.

## Features

- Real-time ASL gesture recognition using your webcam
- Support for all 26 letters of the ASL alphabet (A-Z)
- User progress tracking and statistics dashboard
- Automatic guest user system - no login required
- Hand landmark visualization for better feedback
- Confidence scoring for gesture detection
- PostgreSQL database for persistent storage

## Technology Stack

- **Backend**: Python, Flask, OpenCV, MediaPipe, TensorFlow
- **Frontend**: JavaScript, HTML, CSS, Bootstrap
- **Database**: PostgreSQL with SQLAlchemy ORM

## Setup Instructions

1. **Install Python Dependencies**:
   ```
   pip install flask flask-sqlalchemy gunicorn mediapipe numpy opencv-python psycopg2-binary sqlalchemy tensorflow email-validator
   ```

2. **Database Setup**:
   - Ensure PostgreSQL is installed and running
   - Set the `DATABASE_URL` environment variable with your connection string
   - The application will automatically create the necessary tables

3. **Run the Application**:
   ```
   gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
   ```

4. **Access the Web Interface**:
   - Open a browser and go to `http://localhost:5000`
   - Allow webcam access when prompted
   - Start making ASL gestures!

## Usage

1. Click the "Start" button to enable your webcam
2. Make ASL gestures with your hand
3. Hold a gesture steady until it's recognized
4. Click "Refresh" on the progress dashboard to see your learning statistics

## Advanced Features

- Admin route `/admin/update_database` to update the gesture database
- Adjustable detection threshold in `static/js/main.js`
- Confidence scoring system for more accurate recognition

## License

This project is open source and available under the MIT License.

## Credits

Created using MediaPipe Hands for hand landmark detection and a custom gesture recognition system.