// DOM Elements
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const webcamElement = document.getElementById('webcam');
const overlayCanvas = document.getElementById('overlay');
const loadingIndicator = document.getElementById('loading-indicator');
const webcamStatus = document.getElementById('webcam-status');
const noDetection = document.getElementById('no-detection');
const currentDetection = document.getElementById('current-detection');
const detectedSign = document.getElementById('detected-sign');
const signDescription = document.getElementById('sign-description');
const confidenceBar = document.getElementById('confidence-bar');
const recognizedText = document.getElementById('recognized-text');
const clearTextBtn = document.getElementById('clear-text-btn');
const supportedSigns = document.getElementById('supported-signs');

// Progress dashboard elements
const refreshProgressBtn = document.getElementById('refresh-progress-btn');
const noProgress = document.getElementById('no-progress');
const progressData = document.getElementById('progress-data');
const totalGesturesPracticed = document.getElementById('total-gestures-practiced');
const avgProficiency = document.getElementById('avg-proficiency');
const masteredGestures = document.getElementById('mastered-gestures');
const gestureProficiencyList = document.getElementById('gesture-proficiency-list');

// Variables
let stream = null;
let isRunning = false;
let processingFrame = false;
let lastDetectedSign = null;
let lastDetectionTime = 0;
let detectionBuffer = [];
let recognizedSigns = [];
let context = overlayCanvas.getContext('2d');

// Constants
const DETECTION_THRESHOLD = 0.75; // Increased threshold for more reliable detection
const DETECTION_COOLDOWN = 1500; // 1.5 second cooldown between detections
const SIGN_BUFFER_SIZE = 5; // Increased: Number of consistent detections needed to add a sign

// Initialize the application
async function init() {
    await loadSupportedGestures();
    setupEventListeners();
}

// Load supported gestures from the server
async function loadSupportedGestures() {
    try {
        const response = await fetch('/get_supported_gestures');
        const data = await response.json();
        
        if (data.supported_gestures && data.supported_gestures.length > 0) {
            displaySupportedGestures(data.supported_gestures);
        } else {
            supportedSigns.innerHTML = '<p class="text-warning">No supported gestures found</p>';
        }
    } catch (error) {
        console.error('Error loading supported gestures:', error);
        supportedSigns.innerHTML = '<p class="text-danger">Failed to load supported gestures</p>';
    }
}

// Display supported gestures in the UI
function displaySupportedGestures(gestures) {
    supportedSigns.innerHTML = '';
    
    gestures.forEach(gesture => {
        const col = document.createElement('div');
        col.className = 'col-md-2 col-sm-3 col-4 mb-3';
        
        const card = document.createElement('div');
        card.className = 'card text-center h-100';
        
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body';
        
        const gestureSymbol = document.createElement('h3');
        gestureSymbol.textContent = gesture.name;
        
        const gestureDesc = document.createElement('small');
        gestureDesc.className = 'text-muted';
        gestureDesc.textContent = gesture.description;
        
        cardBody.appendChild(gestureSymbol);
        cardBody.appendChild(gestureDesc);
        card.appendChild(cardBody);
        col.appendChild(card);
        supportedSigns.appendChild(col);
    });
}

// Set up event listeners
function setupEventListeners() {
    startBtn.addEventListener('click', startWebcam);
    stopBtn.addEventListener('click', stopWebcam);
    clearTextBtn.addEventListener('click', clearRecognizedText);
    refreshProgressBtn.addEventListener('click', loadUserProgress);
    
    // Set up overlay canvas size when video metadata is loaded
    webcamElement.addEventListener('loadedmetadata', () => {
        overlayCanvas.width = webcamElement.videoWidth;
        overlayCanvas.height = webcamElement.videoHeight;
    });
    
    // Load initial user progress
    loadUserProgress();
}

// Start the webcam and processing
async function startWebcam() {
    try {
        loadingIndicator.classList.remove('d-none');
        webcamStatus.innerHTML = '<i class="fas fa-circle-notch fa-spin me-2"></i> Initializing webcam...';
        
        // Get webcam access
        stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: 'user'
            },
            audio: false
        });
        
        // Set video source
        webcamElement.srcObject = stream;
        
        // Wait for video to be ready
        await new Promise(resolve => {
            webcamElement.onloadedmetadata = () => {
                // Set canvas size
                overlayCanvas.width = webcamElement.videoWidth;
                overlayCanvas.height = webcamElement.videoHeight;
                resolve();
            };
        });
        
        // Start processing frames
        isRunning = true;
        startBtn.disabled = true;
        stopBtn.disabled = false;
        
        webcamStatus.innerHTML = '<i class="fas fa-check-circle me-2 text-success"></i> Webcam active. Make ASL gestures to translate.';
        webcamStatus.className = 'alert alert-success';
        
        // Start processing frames
        processFrames();
    } catch (error) {
        console.error('Error starting webcam:', error);
        webcamStatus.innerHTML = `<i class="fas fa-exclamation-triangle me-2"></i> Error: ${error.message || 'Could not access webcam'}`;
        webcamStatus.className = 'alert alert-danger';
    } finally {
        loadingIndicator.classList.add('d-none');
    }
}

// Stop the webcam and processing
function stopWebcam() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        webcamElement.srcObject = null;
        stream = null;
    }
    
    isRunning = false;
    startBtn.disabled = false;
    stopBtn.disabled = true;
    
    // Clear canvas
    context.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
    
    // Reset detection display
    noDetection.style.display = 'block';
    currentDetection.classList.add('d-none');
    
    webcamStatus.innerHTML = '<i class="fas fa-info-circle me-2"></i> Click "Start" to enable webcam and begin sign language detection.';
    webcamStatus.className = 'alert alert-info';
}

// Clear the recognized text
function clearRecognizedText() {
    recognizedSigns = [];
    updateRecognizedText();
}

// Process frames from the webcam
async function processFrames() {
    if (!isRunning) return;
    
    if (!processingFrame) {
        processingFrame = true;
        
        try {
            // Capture the current frame
            const frame = await captureFrame();
            
            // Process the frame
            const result = await processFrame(frame);
            
            // Handle the result
            handleResult(result);
        } catch (error) {
            console.error('Error processing frame:', error);
        } finally {
            processingFrame = false;
        }
    }
    
    // Continue processing frames
    requestAnimationFrame(processFrames);
}

// Capture a frame from the webcam
function captureFrame() {
    return new Promise((resolve) => {
        const canvas = document.createElement('canvas');
        canvas.width = webcamElement.videoWidth;
        canvas.height = webcamElement.videoHeight;
        const ctx = canvas.getContext('2d');
        
        // Draw the current video frame to the canvas
        ctx.drawImage(webcamElement, 0, 0, canvas.width, canvas.height);
        
        // Convert canvas to base64 image
        const dataURL = canvas.toDataURL('image/jpeg', 0.8);
        resolve(dataURL);
    });
}

// Process a frame and get the result from the server
async function processFrame(frame) {
    const response = await fetch('/process_frame', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ image: frame })
    });
    
    if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
    }
    
    return await response.json();
}

// Handle the result from the server
function handleResult(result) {
    // Update overlay with the annotated image if available
    if (result.annotated_image) {
        const image = new Image();
        image.onload = function() {
            context.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
            context.drawImage(image, 0, 0, overlayCanvas.width, overlayCanvas.height);
        };
        image.src = result.annotated_image;
    }
    
    // Handle hand detection
    if (result.hand_detected) {
        // Hand is detected but no gesture
        if (!result.gesture_detected) {
            noDetection.style.display = 'block';
            currentDetection.classList.add('d-none');
            lastDetectedSign = null;
            detectionBuffer = [];
        } else {
            // Gesture detected
            const currentTime = Date.now();
            const gesture = result.gesture;
            const confidence = result.confidence;
            
            // Update the gesture display
            noDetection.style.display = 'none';
            currentDetection.classList.remove('d-none');
            detectedSign.textContent = gesture.name;
            signDescription.textContent = gesture.description;
            
            // Update confidence bar
            const confidencePercentage = Math.round(confidence * 100);
            confidenceBar.style.width = `${confidencePercentage}%`;
            confidenceBar.textContent = `${confidencePercentage}%`;
            
            // Color-code based on confidence
            if (confidencePercentage < 50) {
                confidenceBar.className = 'progress-bar bg-danger';
            } else if (confidencePercentage < 75) {
                confidenceBar.className = 'progress-bar bg-warning';
            } else {
                confidenceBar.className = 'progress-bar bg-success';
            }
            
            // Check if this is a new detection after cooldown
            if (currentTime - lastDetectionTime > DETECTION_COOLDOWN && 
                confidence > DETECTION_THRESHOLD) {
                
                // Add to detection buffer
                if (detectionBuffer.length === 0 || 
                    detectionBuffer[detectionBuffer.length - 1] === gesture.name) {
                    detectionBuffer.push(gesture.name);
                    
                    // If buffer reaches threshold, add the sign
                    if (detectionBuffer.length >= SIGN_BUFFER_SIZE && 
                        (lastDetectedSign !== gesture.name)) {
                        
                        recognizedSigns.push(gesture.name);
                        updateRecognizedText();
                        
                        // Save the recognition to the database
                        saveRecognitionToDatabase(gesture.name, confidence);
                        
                        lastDetectedSign = gesture.name;
                        lastDetectionTime = currentTime;
                        detectionBuffer = [];
                    }
                } else {
                    // Different sign, reset buffer
                    detectionBuffer = [gesture.name];
                }
            }
        }
    } else {
        // No hand detected
        noDetection.style.display = 'block';
        currentDetection.classList.add('d-none');
    }
}

// Update the recognized text display
function updateRecognizedText() {
    if (recognizedSigns.length === 0) {
        recognizedText.innerHTML = '<p class="text-muted">Recognized signs will appear here</p>';
    } else {
        recognizedText.innerHTML = '';
        
        // Create a text element for the signs
        const textElement = document.createElement('div');
        textElement.className = 'recognized-signs';
        
        // Create tokens for each sign
        recognizedSigns.forEach(sign => {
            const token = document.createElement('span');
            token.className = 'badge bg-primary me-1 mb-1';
            token.textContent = sign;
            textElement.appendChild(token);
        });
        
        // Add the text element to the container
        recognizedText.appendChild(textElement);
        
        // Add the plain text representation
        const plainText = document.createElement('p');
        plainText.className = 'mt-2';
        plainText.textContent = recognizedSigns.join('');
        recognizedText.appendChild(plainText);
    }
}

// Save a gesture recognition to the database
async function saveRecognitionToDatabase(gestureName, confidence) {
    try {
        const startTime = performance.now();
        const response = await fetch('/save_recognition', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                gesture_name: gestureName,
                confidence: confidence,
                duration_ms: Math.round(performance.now() - startTime),
                success: true
            })
        });
        
        if (!response.ok) {
            console.error('Error saving recognition:', await response.json());
        }
    } catch (error) {
        console.error('Error saving recognition:', error);
    }
}

// Get user progress from the database
async function getUserProgress() {
    try {
        const response = await fetch('/get_user_progress');
        const data = await response.json();
        
        if (response.ok && data.success) {
            return data.progress;
        } else {
            console.error('Error getting user progress:', data.error);
            return [];
        }
    } catch (error) {
        console.error('Error getting user progress:', error);
        return [];
    }
}

// Load and display user progress
async function loadUserProgress() {
    try {
        refreshProgressBtn.disabled = true;
        refreshProgressBtn.innerHTML = '<i class="fas fa-sync-alt fa-spin me-1"></i> Loading...';
        
        // Get progress data from server
        const progress = await getUserProgress();
        
        // Update the progress dashboard
        if (progress && progress.length > 0) {
            // Calculate statistics
            const totalPracticed = progress.length;
            const avgProf = progress.reduce((sum, p) => sum + p.proficiency_level, 0) / totalPracticed;
            const mastered = progress.filter(p => p.proficiency_level >= 80).length;
            
            // Update summary statistics
            totalGesturesPracticed.textContent = totalPracticed;
            avgProficiency.textContent = Math.round(avgProf) + '%';
            masteredGestures.textContent = mastered;
            
            // Show progress data section
            noProgress.classList.add('d-none');
            document.getElementById('progress-data').classList.remove('d-none');
            
            // Update the gesture proficiency list
            updateGestureProficiencyList(progress);
        } else {
            // No progress data available
            noProgress.classList.remove('d-none');
            document.getElementById('progress-data').classList.add('d-none');
        }
    } catch (error) {
        console.error('Error loading user progress:', error);
    } finally {
        refreshProgressBtn.disabled = false;
        refreshProgressBtn.innerHTML = '<i class="fas fa-sync-alt me-1"></i> Refresh';
    }
}

// Update the gesture proficiency list
function updateGestureProficiencyList(progressData) {
    gestureProficiencyList.innerHTML = '';
    
    // Sort progress data by proficiency level (descending)
    const sortedProgress = [...progressData].sort((a, b) => b.proficiency_level - a.proficiency_level);
    
    // Create cards for each gesture
    sortedProgress.forEach(gesture => {
        const col = document.createElement('div');
        col.className = 'col-md-3 col-sm-6 mb-3';
        
        const card = document.createElement('div');
        card.className = 'card h-100';
        
        // Determine card color based on proficiency
        if (gesture.proficiency_level >= 80) {
            card.classList.add('border-success');
        } else if (gesture.proficiency_level >= 50) {
            card.classList.add('border-warning');
        } else {
            card.classList.add('border-info');
        }
        
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body';
        
        const gestureName = document.createElement('h5');
        gestureName.className = 'card-title';
        gestureName.textContent = gesture.gesture_name;
        
        const gestureDesc = document.createElement('p');
        gestureDesc.className = 'card-text small text-muted';
        gestureDesc.textContent = gesture.gesture_description;
        
        const progressBar = document.createElement('div');
        progressBar.className = 'progress mb-2';
        progressBar.style.height = '10px';
        
        const progressBarInner = document.createElement('div');
        progressBarInner.className = 'progress-bar';
        progressBarInner.style.width = `${gesture.proficiency_level}%`;
        progressBarInner.setAttribute('aria-valuenow', gesture.proficiency_level);
        progressBarInner.setAttribute('aria-valuemin', '0');
        progressBarInner.setAttribute('aria-valuemax', '100');
        
        // Set progress bar color based on proficiency
        if (gesture.proficiency_level >= 80) {
            progressBarInner.classList.add('bg-success');
        } else if (gesture.proficiency_level >= 50) {
            progressBarInner.classList.add('bg-warning');
        } else {
            progressBarInner.classList.add('bg-info');
        }
        
        const practiceInfo = document.createElement('p');
        practiceInfo.className = 'card-text d-flex justify-content-between align-items-center mt-2 mb-0';
        
        const profLevel = document.createElement('span');
        profLevel.className = 'badge bg-secondary';
        profLevel.textContent = `${gesture.proficiency_level}% proficiency`;
        
        const practiceCount = document.createElement('small');
        practiceCount.className = 'text-muted';
        practiceCount.textContent = `${gesture.times_practiced} times practiced`;
        
        // Assemble components
        progressBar.appendChild(progressBarInner);
        practiceInfo.appendChild(profLevel);
        practiceInfo.appendChild(practiceCount);
        
        cardBody.appendChild(gestureName);
        cardBody.appendChild(gestureDesc);
        cardBody.appendChild(progressBar);
        cardBody.appendChild(practiceInfo);
        
        card.appendChild(cardBody);
        col.appendChild(card);
        gestureProficiencyList.appendChild(col);
    });
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', init);
