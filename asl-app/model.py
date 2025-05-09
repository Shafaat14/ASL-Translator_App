import cv2
import numpy as np
import mediapipe as mp
import tensorflow as tf
import logging
import base64

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class GestureRecognizer:
    def __init__(self):
        """Initialize the gesture recognizer with MediaPipe Hands"""
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Initialize MediaPipe Hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Define ASL gestures and their meanings
        self.gestures = {
            0: {'name': 'A', 'description': 'Letter A - Fist with thumb pointing up'},
            1: {'name': 'B', 'description': 'Letter B - All fingers extended and together'},
            2: {'name': 'C', 'description': 'Letter C - Fingers together curved in C shape'},
            3: {'name': 'D', 'description': 'Letter D - Index finger pointing up, others closed'},
            4: {'name': 'E', 'description': 'Letter E - All fingers curled, palm facing out'},
            5: {'name': 'F', 'description': 'Letter F - Index finger and thumb touch, other fingers extended'},
            6: {'name': 'G', 'description': 'Letter G - Index pointing, thumb extended'},
            7: {'name': 'H', 'description': 'Letter H - Index and middle finger extended together'},
            8: {'name': 'I', 'description': 'Letter I - Pinky finger extended, others closed'},
            9: {'name': 'J', 'description': 'Letter J - Pinky extended with J motion'},
            10: {'name': 'K', 'description': 'Letter K - Index and middle finger in V, thumb between'},
            11: {'name': 'L', 'description': 'Letter L - Index finger and thumb in L shape'},
            12: {'name': 'M', 'description': 'Letter M - Thumb tucked between folded fingers'},
            13: {'name': 'N', 'description': 'Letter N - Thumb tucked under index and middle fingers'},
            14: {'name': 'O', 'description': 'Letter O - Fingertips and thumb form circle'},
            15: {'name': 'P', 'description': 'Letter P - Index pointing down, thumb to side'},
            16: {'name': 'Q', 'description': 'Letter Q - Finger pointing down, thumb and pinky out'},
            17: {'name': 'R', 'description': 'Letter R - Crossed index and middle fingers'},
            18: {'name': 'S', 'description': 'Letter S - Fist with thumb over fingers'},
            19: {'name': 'T', 'description': 'Letter T - Thumb between index and middle finger'},
            20: {'name': 'U', 'description': 'Letter U - Index and middle finger extended together'},
            21: {'name': 'V', 'description': 'Letter V - Index and middle finger in V shape'},
            22: {'name': 'W', 'description': 'Letter W - Index, middle, and ring fingers extended'},
            23: {'name': 'X', 'description': 'Letter X - Index finger bent at middle joint'},
            24: {'name': 'Y', 'description': 'Letter Y - Thumb and pinky extended, others closed'},
            25: {'name': 'Z', 'description': 'Letter Z - Index finger traces Z shape'}
        }
        
        # Initialize a simple classifier based on hand landmarks
        # In a real application, you would load a pre-trained model here
        self._init_classifier()
        
        logger.debug("GestureRecognizer initialized successfully")
    
    def _init_classifier(self):
        """
        Initialize a simple gesture classifier
        In a production environment, we would use a pre-trained model
        This is a simplified version for demonstration
        """
        # For this demo, we'll use a simple rule-based classification
        # In a real application, you would load a TensorFlow model here
        
        # Define simple rules for each gesture based on finger positions
        self.rules = {
            # A: Fist with thumb pointing up
            0: lambda landmarks: (
                self._is_finger_closed(landmarks, 1) and
                self._is_finger_closed(landmarks, 2) and
                self._is_finger_closed(landmarks, 3) and
                self._is_finger_closed(landmarks, 4) and
                not self._is_finger_closed(landmarks, 0)
            ),
            # B: All fingers extended and together
            1: lambda landmarks: (
                not self._is_finger_closed(landmarks, 1) and
                not self._is_finger_closed(landmarks, 2) and
                not self._is_finger_closed(landmarks, 3) and
                not self._is_finger_closed(landmarks, 4)
            ),
            # C: Fingers together curved in C shape
            2: lambda landmarks: (
                self._get_distance(landmarks[4], landmarks[8]) < 0.1 and
                not self._is_finger_closed(landmarks, 1) and
                not self._is_finger_closed(landmarks, 2) and
                not self._is_finger_closed(landmarks, 3) and
                not self._is_finger_closed(landmarks, 4)
            ),
            # D: Index finger pointing up, others closed
            3: lambda landmarks: (
                not self._is_finger_closed(landmarks, 1) and
                self._is_finger_closed(landmarks, 2) and
                self._is_finger_closed(landmarks, 3) and
                self._is_finger_closed(landmarks, 4)
            ),
            # E: All fingers curled, palm facing out
            4: lambda landmarks: (
                self._is_finger_closed(landmarks, 1) and
                self._is_finger_closed(landmarks, 2) and
                self._is_finger_closed(landmarks, 3) and
                self._is_finger_closed(landmarks, 4)
            ),
            # F: Index finger and thumb touch, other fingers extended
            5: lambda landmarks: (
                self._get_distance(landmarks[4], landmarks[8]) < 0.05 and
                not self._is_finger_closed(landmarks, 2) and
                not self._is_finger_closed(landmarks, 3) and
                not self._is_finger_closed(landmarks, 4)
            ),
            # G: Index pointing, thumb extended
            6: lambda landmarks: (
                not self._is_finger_closed(landmarks, 1) and
                self._is_finger_closed(landmarks, 2) and
                self._is_finger_closed(landmarks, 3) and
                self._is_finger_closed(landmarks, 4) and
                not self._is_finger_closed(landmarks, 0)
            ),
            # H: Index and middle finger extended together
            7: lambda landmarks: (
                not self._is_finger_closed(landmarks, 1) and
                not self._is_finger_closed(landmarks, 2) and
                self._is_finger_closed(landmarks, 3) and
                self._is_finger_closed(landmarks, 4)
            ),
            # I: Pinky finger extended, others closed
            8: lambda landmarks: (
                self._is_finger_closed(landmarks, 1) and
                self._is_finger_closed(landmarks, 2) and
                self._is_finger_closed(landmarks, 3) and
                not self._is_finger_closed(landmarks, 4)
            ),
            # J: Pinky extended and moving in J shape
            9: lambda landmarks: (
                self._is_finger_closed(landmarks, 1) and
                self._is_finger_closed(landmarks, 2) and
                self._is_finger_closed(landmarks, 3) and
                not self._is_finger_closed(landmarks, 4)
            ),
            # K: Index and middle finger in V, thumb between
            10: lambda landmarks: (
                not self._is_finger_closed(landmarks, 1) and
                not self._is_finger_closed(landmarks, 2) and
                self._is_finger_closed(landmarks, 3) and
                self._is_finger_closed(landmarks, 4) and
                self._get_distance(landmarks[4], landmarks[10]) < 0.1
            ),
            # L: Index finger and thumb in L shape
            11: lambda landmarks: (
                not self._is_finger_closed(landmarks, 1) and
                self._is_finger_closed(landmarks, 2) and
                self._is_finger_closed(landmarks, 3) and
                self._is_finger_closed(landmarks, 4) and
                landmarks[4].x > landmarks[3].x
            ),
            # M: Thumb tucked between folded fingers
            12: lambda landmarks: (
                self._is_finger_closed(landmarks, 1) and
                self._is_finger_closed(landmarks, 2) and
                self._is_finger_closed(landmarks, 3) and
                landmarks[4].x < landmarks[5].x
            ),
            # N: Thumb tucked under index and middle fingers
            13: lambda landmarks: (
                self._is_finger_closed(landmarks, 1) and
                self._is_finger_closed(landmarks, 2) and
                self._is_finger_closed(landmarks, 3) and
                self._is_finger_closed(landmarks, 4) and
                landmarks[4].x < landmarks[9].x
            ),
            # O: Fingertips and thumb form circle
            14: lambda landmarks: (
                self._get_distance(landmarks[4], landmarks[8]) < 0.08
            ),
            # P: Index pointing down, thumb to side
            15: lambda landmarks: (
                not self._is_finger_closed(landmarks, 1) and
                self._is_finger_closed(landmarks, 2) and
                self._is_finger_closed(landmarks, 3) and
                self._is_finger_closed(landmarks, 4) and
                landmarks[8].y > landmarks[5].y
            ),
            # Q: Finger pointing down, thumb and pinky out
            16: lambda landmarks: (
                not self._is_finger_closed(landmarks, 1) and
                self._is_finger_closed(landmarks, 2) and
                self._is_finger_closed(landmarks, 3) and
                not self._is_finger_closed(landmarks, 4) and
                landmarks[8].y > landmarks[5].y
            ),
            # R: Crossed index and middle fingers
            17: lambda landmarks: (
                not self._is_finger_closed(landmarks, 1) and
                not self._is_finger_closed(landmarks, 2) and
                self._is_finger_closed(landmarks, 3) and
                self._is_finger_closed(landmarks, 4) and
                self._get_distance(landmarks[8], landmarks[12]) < 0.1
            ),
            # S: Fist with thumb over fingers
            18: lambda landmarks: (
                self._is_finger_closed(landmarks, 1) and
                self._is_finger_closed(landmarks, 2) and
                self._is_finger_closed(landmarks, 3) and
                self._is_finger_closed(landmarks, 4) and
                landmarks[4].z < landmarks[8].z
            ),
            # T: Thumb between index and middle finger
            19: lambda landmarks: (
                self._is_finger_closed(landmarks, 1) and
                self._is_finger_closed(landmarks, 2) and
                self._is_finger_closed(landmarks, 3) and
                self._is_finger_closed(landmarks, 4) and
                landmarks[4].x > landmarks[6].x and landmarks[4].x < landmarks[10].x
            ),
            # U: Index and middle finger extended together
            20: lambda landmarks: (
                not self._is_finger_closed(landmarks, 1) and
                not self._is_finger_closed(landmarks, 2) and
                self._is_finger_closed(landmarks, 3) and
                self._is_finger_closed(landmarks, 4) and
                self._get_distance(landmarks[8], landmarks[12]) < 0.15
            ),
            # V: Index and middle finger in V shape
            21: lambda landmarks: (
                not self._is_finger_closed(landmarks, 1) and
                not self._is_finger_closed(landmarks, 2) and
                self._is_finger_closed(landmarks, 3) and
                self._is_finger_closed(landmarks, 4) and
                self._get_distance(landmarks[8], landmarks[12]) > 0.15
            ),
            # W: Index, middle, and ring fingers extended
            22: lambda landmarks: (
                not self._is_finger_closed(landmarks, 1) and
                not self._is_finger_closed(landmarks, 2) and
                not self._is_finger_closed(landmarks, 3) and
                self._is_finger_closed(landmarks, 4)
            ),
            # X: Index finger bent at middle joint
            23: lambda landmarks: (
                landmarks[8].y > landmarks[7].y and
                landmarks[7].y < landmarks[6].y and
                self._is_finger_closed(landmarks, 2) and
                self._is_finger_closed(landmarks, 3) and
                self._is_finger_closed(landmarks, 4)
            ),
            # Y: Thumb and pinky extended, others closed
            24: lambda landmarks: (
                self._is_finger_closed(landmarks, 1) and
                self._is_finger_closed(landmarks, 2) and
                self._is_finger_closed(landmarks, 3) and
                not self._is_finger_closed(landmarks, 4) and
                not self._is_finger_closed(landmarks, 0)
            ),
            # Z: Index finger traces Z shape - simplified as extended index
            25: lambda landmarks: (
                not self._is_finger_closed(landmarks, 1) and
                self._is_finger_closed(landmarks, 2) and
                self._is_finger_closed(landmarks, 3) and
                self._is_finger_closed(landmarks, 4) and
                landmarks[8].y > landmarks[5].y
            )
        }
    
    def _is_finger_closed(self, landmarks, finger_idx):
        """Check if a finger is closed based on the landmarks"""
        if finger_idx == 0:  # Thumb
            return (landmarks[3].y > landmarks[4].y)
        else:
            # Get the base, middle, and tip of the finger
            base_idx = finger_idx * 4 + 1
            middle_idx = finger_idx * 4 + 2
            tip_idx = finger_idx * 4 + 3
            
            # Calculate distances
            base_to_middle = self._get_distance(landmarks[base_idx], landmarks[middle_idx])
            middle_to_tip = self._get_distance(landmarks[middle_idx], landmarks[tip_idx])
            base_to_tip = self._get_distance(landmarks[base_idx], landmarks[tip_idx])
            
            # If the tip is closer to the base than the length of the finger, the finger is closed
            return base_to_tip < (base_to_middle + middle_to_tip) * 0.7
    
    def _get_distance(self, landmark1, landmark2):
        """Calculate Euclidean distance between two landmarks"""
        return np.sqrt(
            (landmark1.x - landmark2.x)**2 + 
            (landmark1.y - landmark2.y)**2 + 
            (landmark1.z - landmark2.z)**2
        )
    
    def get_supported_gestures(self):
        """Return the list of supported gestures"""
        return list(self.gestures.values())
    
    def process_frame(self, frame):
        """Process a frame and recognize hand gestures"""
        # Convert the BGR image to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame with MediaPipe Hands
        results = self.hands.process(rgb_frame)
        
        # Prepare return data
        response = {
            'hand_detected': False,
            'gesture_detected': False,
            'gesture': None,
            'confidence': 0.0,
            'landmarks': None
        }
        
        # Draw hand landmarks on the frame
        annotated_frame = frame.copy()
        
        if results.multi_hand_landmarks:
            response['hand_detected'] = True
            
            # Get the first hand landmarks
            hand_landmarks = results.multi_hand_landmarks[0]
            
            # Draw landmarks on the frame
            self.mp_drawing.draw_landmarks(
                annotated_frame,
                hand_landmarks,
                self.mp_hands.HAND_CONNECTIONS,
                self.mp_drawing_styles.get_default_hand_landmarks_style(),
                self.mp_drawing_styles.get_default_hand_connections_style()
            )
            
            # Convert landmarks to a list format for response
            landmarks_list = []
            for landmark in hand_landmarks.landmark:
                landmarks_list.append({
                    'x': landmark.x,
                    'y': landmark.y,
                    'z': landmark.z
                })
            
            response['landmarks'] = landmarks_list
            
            # Recognize the gesture
            gesture_id, confidence = self._recognize_gesture(hand_landmarks.landmark)
            if gesture_id is not None and confidence > 0.6:
                response['gesture_detected'] = True
                response['gesture'] = self.gestures[gesture_id]
                response['confidence'] = confidence
        
        # Convert the annotated frame to base64 to send back to frontend
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        annotated_image_base64 = base64.b64encode(buffer).decode('utf-8')
        response['annotated_image'] = f"data:image/jpeg;base64,{annotated_image_base64}"
        
        return response
    
    def _recognize_gesture(self, landmarks):
        """
        Recognize a gesture based on hand landmarks
        Returns (gesture_id, confidence)
        """
        # For this demo, we'll use our rule-based classification
        # In a real application, you would use a trained model
        
        # Make recognition more strict - increase threshold
        best_gesture = None
        best_confidence = 0.0
        
        for gesture_id, rule_func in self.rules.items():
            try:
                # Check how well the rule matches by measuring distance or similarity
                # For now, we use a simple boolean match with a fixed confidence
                if rule_func(landmarks):
                    confidence = self._get_gesture_confidence(landmarks, gesture_id)
                    if confidence > best_confidence:
                        best_gesture = gesture_id
                        best_confidence = confidence
            except Exception as e:
                logger.error(f"Error applying rule for gesture {gesture_id}: {e}")
        
        # Increase minimum threshold for detection to reduce false positives
        if best_confidence > 0.7:  # Higher threshold for confidence
            return best_gesture, best_confidence
        
        # If no rule matches with enough confidence, return None
        return None, 0.0
        
    def _get_gesture_confidence(self, landmarks, gesture_id):
        """Calculate a confidence score for a gesture based on landmark positions"""
        # This is a simplified version - in a real app, you would calculate 
        # how closely the landmarks match the expected pattern
        
        # Base confidence level
        confidence = 0.75
        
        # For "A" gesture (thumbs up), check if thumb is really extended
        if gesture_id == 0:  # A
            # If thumb is very clearly extended, increase confidence
            if landmarks[4].y < landmarks[3].y - 0.1:
                confidence += 0.15
                
        # For "B" gesture, check if all fingers are clearly extended
        elif gesture_id == 1:  # B
            # Count extended fingers
            extended_fingers = 0
            for i in range(1, 5):  # Index through pinky
                if not self._is_finger_closed(landmarks, i):
                    extended_fingers += 1
            
            # All 4 fingers should be extended for "B"
            if extended_fingers == 4:
                confidence += 0.15
            else:
                confidence -= 0.3
                
        # For "C" gesture, check if fingers form a clear C shape
        elif gesture_id == 2:  # C
            if 0.05 < self._get_distance(landmarks[4], landmarks[8]) < 0.15:
                confidence += 0.15
                
        # For "D" gesture, check if index is clearly extended and others closed
        elif gesture_id == 3:  # D
            if not self._is_finger_closed(landmarks, 1) and self._is_finger_closed(landmarks, 2):
                confidence += 0.15
                
        # For "L" gesture, check if thumb and index form a clear L shape
        elif gesture_id == 11:  # L
            if not self._is_finger_closed(landmarks, 1) and landmarks[4].x > landmarks[3].x:
                confidence += 0.15
                
        # For "O" gesture, check if thumb and index form a clear circle
        elif gesture_id == 14:  # O
            if 0.05 < self._get_distance(landmarks[4], landmarks[8]) < 0.1:
                confidence += 0.15
                
        # For "V" gesture, check if fingers form a clear V shape
        elif gesture_id == 21:  # V
            if not self._is_finger_closed(landmarks, 1) and not self._is_finger_closed(landmarks, 2):
                if self._get_distance(landmarks[8], landmarks[12]) > 0.2:
                    confidence += 0.15
                    
        # For "W" gesture, check if three fingers are clearly extended
        elif gesture_id == 22:  # W
            extended_fingers = 0
            for i in range(1, 4):  # Index through ring
                if not self._is_finger_closed(landmarks, i):
                    extended_fingers += 1
            
            if extended_fingers == 3:
                confidence += 0.15
                
        # For "Y" gesture, check if thumb and pinky are clearly extended
        elif gesture_id == 24:  # Y
            if not self._is_finger_closed(landmarks, 4) and not self._is_finger_closed(landmarks, 0):
                confidence += 0.15
                
        # General confidence adjustments for all gestures
        
        # Penalize ambiguous hand positions
        for other_id, rule_func in self.rules.items():
            if other_id != gesture_id:
                try:
                    if rule_func(landmarks):
                        # Another rule also matches, reduce confidence
                        confidence -= 0.1
                except Exception:
                    pass
                    
        # Increase confidence if hand is clearly visible and centered
        if 0.2 < landmarks[0].x < 0.8 and 0.2 < landmarks[0].y < 0.8:
            confidence += 0.05
        
        # Ensure confidence is within valid range
        return max(0.0, min(confidence, 1.0))
