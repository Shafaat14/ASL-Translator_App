/**
 * Gesture Recognizer - Client-side utilities for sign language detection
 * 
 * This module provides helper functions and utilities for handling
 * sign language gestures in the browser. It complements the server-side
 * recognition with client-side visualization and gesture processing.
 */

class GestureRecognizer {
    constructor() {
        // Configuration settings
        this.config = {
            // Minimum confidence level for recognizing a gesture (0-1)
            confidenceThreshold: 0.6,
            
            // Time in ms to wait before accepting another gesture
            detectionCooldown: 1000,
            
            // Number of consistent detections needed to confirm a gesture
            bufferSize: 3,
            
            // Debug mode
            debug: false
        };
        
        // State variables
        this.state = {
            lastDetectedGesture: null,
            lastDetectionTime: 0,
            detectionBuffer: [],
            recognizedGestures: []
        };
        
        // Gesture descriptions for reference
        this.gestureDescriptions = {
            'A': 'Fist with thumb pointing up',
            'B': 'All fingers extended and together',
            'C': 'Fingers together curved in C shape',
            'D': 'Index finger pointing up, others closed',
            'E': 'All fingers curled, palm facing out',
            'F': 'Index finger and thumb touch, other fingers extended',
            'G': 'Index pointing, thumb extended',
            'H': 'Index and middle finger extended together',
            'I': 'Pinky finger extended, others closed',
            'J': 'Pinky extended with J motion'
        };
    }
    
    /**
     * Process a detection result from the server
     * @param {Object} result - The detection result from the server
     * @param {Function} onGestureDetected - Callback when new gesture is detected
     * @returns {Object} - Processed result with additional client-side information
     */
    processDetection(result, onGestureDetected) {
        // Create a processed result object
        const processedResult = {
            isHandDetected: result.hand_detected,
            isGestureDetected: result.gesture_detected,
            gesture: result.gesture,
            confidence: result.confidence,
            shouldAddToText: false,
            bufferFull: false,
            bufferProgress: 0
        };
        
        // If no hand detected, reset state
        if (!result.hand_detected) {
            this.resetDetectionState();
            return processedResult;
        }
        
        // If hand detected but no gesture recognized
        if (!result.gesture_detected) {
            this.resetDetectionState();
            return processedResult;
        }
        
        // Handle detected gesture
        const currentTime = Date.now();
        const gestureName = result.gesture.name;
        const confidence = result.confidence;
        
        // Check if gesture is confident enough and cooldown has passed
        if (confidence > this.config.confidenceThreshold && 
            (currentTime - this.state.lastDetectionTime > this.config.detectionCooldown)) {
            
            // Calculate buffer state
            if (this.state.detectionBuffer.length === 0 || 
                this.state.detectionBuffer[this.state.detectionBuffer.length - 1] === gestureName) {
                
                // Add to the buffer
                this.state.detectionBuffer.push(gestureName);
                
                // Calculate buffer progress
                processedResult.bufferProgress = 
                    (this.state.detectionBuffer.length / this.config.bufferSize) * 100;
                
                // Check if buffer is full
                if (this.state.detectionBuffer.length >= this.config.bufferSize && 
                    this.state.lastDetectedGesture !== gestureName) {
                    
                    // Buffer is full and gesture is new
                    processedResult.shouldAddToText = true;
                    processedResult.bufferFull = true;
                    
                    // Call callback if provided
                    if (onGestureDetected && typeof onGestureDetected === 'function') {
                        onGestureDetected(gestureName);
                    }
                    
                    // Update state
                    this.state.lastDetectedGesture = gestureName;
                    this.state.lastDetectionTime = currentTime;
                    this.state.detectionBuffer = [];
                }
            } else {
                // Different sign detected, reset buffer
                this.state.detectionBuffer = [gestureName];
                processedResult.bufferProgress = 
                    (this.state.detectionBuffer.length / this.config.bufferSize) * 100;
            }
        }
        
        return processedResult;
    }
    
    /**
     * Reset the detection state
     */
    resetDetectionState() {
        this.state.detectionBuffer = [];
    }
    
    /**
     * Add a gesture to the recognized list
     * @param {string} gesture - The gesture to add
     */
    addRecognizedGesture(gesture) {
        this.state.recognizedGestures.push(gesture);
    }
    
    /**
     * Get all recognized gestures
     * @returns {Array} - List of recognized gestures
     */
    getRecognizedGestures() {
        return [...this.state.recognizedGestures];
    }
    
    /**
     * Clear recognized gestures
     */
    clearRecognizedGestures() {
        this.state.recognizedGestures = [];
    }
    
    /**
     * Get the description of a gesture
     * @param {string} gesture - The gesture name
     * @returns {string} - The description of the gesture
     */
    getGestureDescription(gesture) {
        return this.gestureDescriptions[gesture] || 'Unknown gesture';
    }
    
    /**
     * Get all supported gestures with descriptions
     * @returns {Object} - Map of gesture names to descriptions
     */
    getSupportedGestures() {
        return {...this.gestureDescriptions};
    }
    
    /**
     * Update configuration options
     * @param {Object} options - New configuration options
     */
    updateConfig(options) {
        this.config = {...this.config, ...options};
    }
    
    /**
     * Draw hand landmarks on a canvas
     * @param {Object} landmarks - Hand landmarks from MediaPipe
     * @param {CanvasRenderingContext2D} ctx - Canvas context to draw on
     * @param {number} width - Canvas width
     * @param {number} height - Canvas height
     */
    drawHandLandmarks(landmarks, ctx, width, height) {
        if (!landmarks || !ctx) return;
        
        // Connection pairs for fingers
        const fingerConnections = [
            // Thumb
            [0, 1], [1, 2], [2, 3], [3, 4],
            // Index finger
            [0, 5], [5, 6], [6, 7], [7, 8],
            // Middle finger
            [0, 9], [9, 10], [10, 11], [11, 12],
            // Ring finger
            [0, 13], [13, 14], [14, 15], [15, 16],
            // Pinky
            [0, 17], [17, 18], [18, 19], [19, 20],
            // Palm
            [0, 5], [5, 9], [9, 13], [13, 17]
        ];
        
        // Clear the canvas
        ctx.clearRect(0, 0, width, height);
        
        // Draw connections
        ctx.strokeStyle = 'rgba(0, 255, 0, 0.8)';
        ctx.lineWidth = 3;
        
        fingerConnections.forEach(connection => {
            const [i, j] = connection;
            if (landmarks[i] && landmarks[j]) {
                ctx.beginPath();
                ctx.moveTo(landmarks[i].x * width, landmarks[i].y * height);
                ctx.lineTo(landmarks[j].x * width, landmarks[j].y * height);
                ctx.stroke();
            }
        });
        
        // Draw landmarks
        landmarks.forEach(landmark => {
            ctx.fillStyle = 'rgba(255, 0, 0, 0.8)';
            ctx.beginPath();
            ctx.arc(landmark.x * width, landmark.y * height, 5, 0, 2 * Math.PI);
            ctx.fill();
        });
    }
    
    /**
     * Visualize a gesture detection result
     * @param {Object} result - Detection result
     * @param {HTMLElement} container - Container element to update
     */
    visualizeDetection(result, container) {
        if (!container) return;
        
        // Create HTML for the visualization
        let html = '';
        
        if (!result.isHandDetected) {
            // No hand detected
            html = `
                <div class="text-center text-muted">
                    <i class="fas fa-hand-paper fa-3x mb-2"></i>
                    <p>No hand detected</p>
                </div>
            `;
        } else if (!result.isGestureDetected) {
            // Hand detected but no gesture recognized
            html = `
                <div class="text-center text-muted">
                    <i class="fas fa-question-circle fa-3x mb-2"></i>
                    <p>Hand detected, no gesture recognized</p>
                </div>
            `;
        } else {
            // Gesture detected
            const confidencePercentage = Math.round(result.confidence * 100);
            let confidenceClass = 'bg-danger';
            
            if (confidencePercentage >= 75) {
                confidenceClass = 'bg-success';
            } else if (confidencePercentage >= 50) {
                confidenceClass = 'bg-warning';
            }
            
            // Buffer progress indicator
            let bufferHtml = '';
            if (result.bufferProgress > 0) {
                bufferHtml = `
                    <div class="mt-2">
                        <small>Recognition progress:</small>
                        <div class="progress">
                            <div class="progress-bar bg-info" role="progressbar" 
                                style="width: ${result.bufferProgress}%" 
                                aria-valuenow="${result.bufferProgress}" 
                                aria-valuemin="0" 
                                aria-valuemax="100"></div>
                        </div>
                    </div>
                `;
            }
            
            html = `
                <div class="text-center">
                    <h2 class="mb-2">${result.gesture.name}</h2>
                    <p>${result.gesture.description}</p>
                    <div class="progress mb-2">
                        <div class="progress-bar ${confidenceClass}" role="progressbar" 
                            style="width: ${confidencePercentage}%" 
                            aria-valuenow="${confidencePercentage}" 
                            aria-valuemin="0" 
                            aria-valuemax="100">${confidencePercentage}%</div>
                    </div>
                    ${bufferHtml}
                </div>
            `;
        }
        
        // Update the container
        container.innerHTML = html;
    }
    
    /**
     * Format recognized gestures to show in the UI
     * @param {Array} gestures - List of recognized gestures
     * @param {HTMLElement} container - Container element to update
     */
    formatRecognizedGestures(gestures, container) {
        if (!container) return;
        
        if (gestures.length === 0) {
            container.innerHTML = '<p class="text-muted">Recognized signs will appear here</p>';
            return;
        }
        
        // Create tokens for each gesture
        const tokensHtml = gestures.map(gesture => 
            `<span class="badge bg-primary me-1 mb-1">${gesture}</span>`
        ).join('');
        
        // Create the full text
        const textString = gestures.join('');
        
        // Update container
        container.innerHTML = `
            <div class="recognized-signs">
                ${tokensHtml}
            </div>
            <p class="mt-2">${textString}</p>
        `;
    }
    
    /**
     * Log debugging information
     * @param {string} message - Debug message
     * @param {any} data - Optional data to log
     */
    debug(message, data) {
        if (this.config.debug) {
            console.log(`[GestureRecognizer] ${message}`, data || '');
        }
    }
}

// Create singleton instance
const gestureRecognizer = new GestureRecognizer();

// Export for module use if needed
if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
    module.exports = gestureRecognizer;
}
