/**
 * Main application logic
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize webcam handler
    const webcamHandler = new WebcamHandler();
    
    // UI elements
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const clearBtn = document.getElementById('clearBtn');
    const resultsDiv = document.getElementById('recognition-results');
    
    // Keep track of recognized letters
    let recognizedText = '';
    
    // Event listeners for buttons
    startBtn.addEventListener('click', startWebcam);
    stopBtn.addEventListener('click', stopWebcam);
    clearBtn.addEventListener('click', clearRecognition);
    
    // Listen for sign recognition events
    document.addEventListener('signRecognized', handleSignRecognition);
    
    /**
     * Starts the webcam and recognition process
     */
    async function startWebcam() {
        try {
            // Show loading state
            startBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Starting...';
            startBtn.disabled = true;
            
            // Initialize and start the camera
            await webcamHandler.initCamera();
            webcamHandler.startProcessing();
            
            // Update UI
            startBtn.disabled = true;
            stopBtn.disabled = false;
            
            // Reset the recognition results
            updateEmptyState();
            
            startBtn.innerHTML = '<i class="fas fa-play me-1"></i> Start Camera';
        } catch (error) {
            console.error('Failed to start webcam:', error);
            startBtn.disabled = false;
            startBtn.innerHTML = '<i class="fas fa-play me-1"></i> Start Camera';
            
            // Show error in results area
            resultsDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Could not access webcam. Please check your camera permissions.
                </div>
            `;
        }
    }
    
    /**
     * Stops the webcam and recognition process
     */
    function stopWebcam() {
        webcamHandler.stopProcessing();
        
        // Update UI
        startBtn.disabled = false;
        stopBtn.disabled = true;
    }
    
    /**
     * Clears the current recognition results
     */
    function clearRecognition() {
        recognizedText = '';
        updateEmptyState();
    }
    
    /**
     * Handles a sign recognition event
     * @param {CustomEvent} event - The sign recognition event
     */
    function handleSignRecognition(event) {
        const { text, confidence } = event.detail;
        
        if (text && confidence > 0.5) {
            // Add the recognized letter if it's different from the last one
            const lastLetter = recognizedText.slice(-1);
            
            if (lastLetter !== text) {
                recognizedText += text;
                updateRecognitionResults();
            }
        }
    }
    
    /**
     * Updates the recognition results in the UI
     */
    function updateRecognitionResults() {
        if (!recognizedText) {
            updateEmptyState();
            return;
        }
        
        // Split the recognized text into characters for display
        const characters = recognizedText.split('');
        
        // Create HTML for the results
        let html = '<div class="recognized-content">';
        html += '<div class="recognized-text mb-3">' + recognizedText + '</div>';
        
        html += '<div class="character-grid">';
        characters.forEach(char => {
            html += `
                <div class="character-item">
                    <span class="character">${char}</span>
                </div>
            `;
        });
        html += '</div>';
        
        html += '</div>';
        
        // Update the results container
        resultsDiv.innerHTML = html;
    }
    
    /**
     * Shows the empty state in the recognition results
     */
    function updateEmptyState() {
        resultsDiv.innerHTML = `
            <div class="text-center text-muted empty-state">
                <i class="fas fa-hand-paper mb-3" style="font-size: 3rem;"></i>
                <p>No signs recognized yet. Start the camera and perform ASL signs.</p>
            </div>
        `;
    }
});
