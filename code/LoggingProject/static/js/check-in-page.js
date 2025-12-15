document.addEventListener('DOMContentLoaded', function() {

    // Global variables
    let mode = "check-in";
    const errorMessageElement = document.getElementById('errorMessage');
    const scanQrButton = document.getElementById('scan-qr-button');
    const qrVideo = document.getElementById('qr-video');
    const uhIdInput = document.querySelector('#uh-id-input input[name="student_id"]');
    let qrScannerActive = false;

    // 1. Handle Mode (Check-In / Check-Out) Radio
    const modeRadios = document.querySelectorAll('input[name="mode"]');
    modeRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            mode = document.querySelector('input[name="mode"]:checked').value;
        });
    });

    // 2. Scan QR Code Button Click Handler
    scanQrButton.addEventListener('click', function() {
        if (!qrScannerActive) {
            startQrScanner();
        } else {
            stopQrScanner();
        }
    });

    // 3. Start QR Scanner (Activate Front Facing Camera)
    function startQrScanner() {
        // Unhide the video element
        qrVideo.classList.remove('hidden');
        qrVideo.style.display = 'block'; 
        // Access the front-facing camera
        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } })
            .then(function(stream) {
                qrVideo.srcObject = stream;
                qrVideo.play();
                qrScannerActive = true;
                scanQrButton.textContent = "Stop Scanning QR Code"; // Change button text
                requestAnimationFrame(scanQrCode); // Start scanning loop
            })
            .catch(function(error) {
                console.error('Error accessing the camera: ', error);
                errorMessageElement.textContent = "Error: Could not access the camera.";
                errorMessageElement.className = "error-message"; 
            });
    }

    // 4. Stop QR Scanner (Deactivate Front Facing Camera)
    function stopQrScanner() {
        qrScannerActive = false;
        scanQrButton.textContent = "Scan QR Code"; // Reset button text
        qrVideo.classList.add('hidden');
        qrVideo.style.display = 'none';
        const stream = qrVideo.srcObject;
        if (stream) {
            const tracks = stream.getTracks();
            tracks.forEach(track => track.stop()); // Stop camera stream
        }
    }

    // 5. QR Code Scanning Loop
    function scanQrCode() {
        if (!qrScannerActive) return; // Stop scanning if the scanner is not active

        if (qrVideo.readyState === qrVideo.HAVE_ENOUGH_DATA) {
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            canvas.width = qrVideo.videoWidth;
            canvas.height = qrVideo.videoHeight;
            context.drawImage(qrVideo, 0, 0, canvas.width, canvas.height);

            const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
            const qrCode = jsQR(imageData.data, canvas.width, canvas.height);

            if (qrCode) {
                let studentId = qrCode.data; 
            
                // Remove leading zeroes using a regular expression
                studentId = studentId.replace(/^0+/, ''); 
            
                // Set the processed student ID into the UH ID input field
                uhIdInput.value = studentId;
            
                stopQrScanner(); // Stop the scanner after successful scan
                form.submit(); 
            }
        }

        // Keep scanning
        if (qrScannerActive) {
            requestAnimationFrame(scanQrCode);
        }
    }

    // 6. Intercept form submission to parse the UH ID if needed
    const form = document.querySelector('form');
    form.addEventListener('submit', function(event) {
        const selectedMethod = document.querySelector('input[name="checkin-method"]:checked').value;

        errorMessageElement.textContent = "";

        // If the user is using cougar card ID, parse it with extractUhid
        if (selectedMethod === 'uh-id') {
            const rawValue = uhIdInput.value;
            const extracted = extractUhid(rawValue);

            if (extracted) {
                uhIdInput.value = extracted;
            } else {
                event.preventDefault();
                errorMessageElement.textContent = `Error: No check-in record found for student with ID: ${rawValue}`;
                errorMessageElement.className = "error-message"; 
            }
        }
    });
});

// 7. Handle toggle switches for Checkin/Checkout and input mode
document.addEventListener("DOMContentLoaded", function () {
    const modeSwitch = document.getElementById("mode-switch");
    const checkinLabel = document.getElementById("checkin-label");
    const checkoutLabel = document.getElementById("checkout-label");

    function updateLabels() {
        if (modeSwitch.checked) {
            checkinLabel.style.color = "#888"; // Unselected
            checkoutLabel.style.color = "#000"; // Selected
        } else {
            checkinLabel.style.color = "#000";
            checkoutLabel.style.color = "#888";
        }
    }

    modeSwitch.addEventListener("change", updateLabels);
    updateLabels();
});
