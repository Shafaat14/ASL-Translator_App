/**
 * WebcamHandler - Handles all webcam-related operations
 */
class WebcamHandler {
    constructor() {
        this.video = document.getElementById('webcam');
        this.canvas = document.getElementById('canvas');
        this.ctx = this.canvas.getContext('2d');
        this.videoStream = null;
        this.processingInterval = null;
        this.isRunning = false;
        
        // Configure canvas size
        this.canvas.width = 640;
        this.canvas.height = 480;
    }

    /**
     * Initializes the webcam stream
     */
    async initCamera() {
        try {
            const constraints = {
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                }
            };
            
            this.videoStream = await navigator.mediaDevices.getUserMedia(constraints);
            this.video.srcObject = this.videoStream;
            
            return new Promise((resolve) => {
                this.video.onloadedmetadata = () => {
                    resolve(true);
                };
            });
        } catch (error) {
            console.error('Error accessing webcam:', error);
            this.showErrorMessage('Camera access denied or not available. Please check your camera permissions.');
            return Promise.reject(error);
        }
    }

    /**
     * Starts webcam processing
     */
    startProcessing() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        
        // Process frames every 100ms (10fps)
        this.processingInterval = setInterval(() => {
            this.captureFrame();
        }, 100);
    }

    /**
     * Stops webcam processing
     */
    stopProcessing() {
        if (!this.isRunning) return;
        
        this.isRunning = false;
        
        if (this.processingInterval) {
            clearInterval(this.processingInterval);
            this.processingInterval = null;
        }
        
        if (this.videoStream) {
            this.videoStream.getTracks().forEach(track => track.stop());
            this.videoStream = null;
            this.video.srcObject = null;
        }
    }

    /**
     * Captures a frame from the webcam
     */
    captureFrame() {
        if (!this.isRunning || !this.video.videoWidth) return;
        
        // Adjust canvas size to match video dimensions
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        
        // Draw the current video frame to the canvas
        this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
        
        // Convert the frame to base64 for sending to the server
        const imageData = this.canvas.toDataURL('image/jpeg', 0.8);
        
        // Send the frame for processing
        this.sendFrameForProcessing(imageData);
    }

    /**
     * Sends a frame to the server for processing
     * @param {string} imageData - Base64 encoded image data
     */
    sendFrameForProcessing(imageData) {
        fetch('/process_frame', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ image: imageData })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error processing frame:', data.error);
                return;
            }
            
            // Handle the processed data
            if (data.recognized_text) {
                // Update the UI with the recognized sign
                document.dispatchEvent(new CustomEvent('signRecognized', {
                    detail: {
                        text: data.recognized_text,
                        confidence: data.confidence
                    }
                }));
            }
        })
        .catch(error => {
            console.error('Error sending frame for processing:', error);
        });
    }

    /**
     * Shows an error message to the user
     * @param {string} message - The error message to display
     */
    showErrorMessage(message) {
        const resultsDiv = document.getElementById('recognition-results');
        resultsDiv.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
            </div>
        `;
    }
}

// Export the WebcamHandler
window.WebcamHandler = WebcamHandler;
