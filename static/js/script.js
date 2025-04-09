/**
 * Initialize file upload functionality
 */
function initFileUpload() {
    // Get DOM elements with null checks
    const fileInput = document.getElementById('videoInput');
    const uploadMessage = document.getElementById('uploadMessage');
    const uploadForm = document.getElementById('uploadForm');
    
    // Exit early if required elements don't exist
    if (!fileInput || !uploadForm) {
        console.warn('File upload initialization failed: required elements not found');
        return;
    }
    
    // Get progress bar elements, with null checks
    const progressBar = document.getElementById('uploadProgress');
    let progressBarInner = null;
    if (progressBar) {
        progressBarInner = progressBar.querySelector('.progress-bar');
    }

    // Helper functions for drag and drop
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight() {
        if (uploadMessage) {
            uploadMessage.classList.add('highlight');
        }
    }

    function unhighlight() {
        if (uploadMessage) {
            uploadMessage.classList.remove('highlight');
        }
    }

    function handleDrop(e) {
        if (!fileInput) return;
        
        const dt = e.dataTransfer;
        const files = dt.files;
        fileInput.files = files;
        
        // Update UI to show selected file
        if (files.length > 0 && uploadMessage) {
            uploadMessage.innerHTML = `
                <i class="fas fa-file-video fa-2x mb-2"></i>
                <p class="mb-0">${files[0].name}</p>
                <p class="text-muted small">${formatFileSize(files[0].size)}</p>
            `;
        }
    }

    // Handle drag and drop if uploadMessage exists
    if (uploadMessage) {
        // Add event listeners for drag and drop
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadMessage.addEventListener(eventName, preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadMessage.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadMessage.addEventListener(eventName, unhighlight, false);
        });

        uploadMessage.addEventListener('drop', handleDrop, false);

        // Handle file input change
        if (fileInput) {
            fileInput.addEventListener('change', function() {
                if (this.files.length > 0 && uploadMessage) {
                    uploadMessage.innerHTML = `
                        <i class="fas fa-file-video fa-2x mb-2"></i>
                        <p class="mb-0">${this.files[0].name}</p>
                        <p class="text-muted small">${formatFileSize(this.files[0].size)}</p>
                    `;
                }
            });
        }

        // Handle click on upload area
        uploadMessage.addEventListener('click', function() {
            if (fileInput) {
                fileInput.click();
            }
        });
    }

    // Handle form submission with progress
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            
            if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
                showAlert('Please select a video file first', 'danger');
                return;
            }
            
            // Show progress bar if it exists
            if (progressBar) {
                progressBar.classList.remove('d-none');
            }
            
            // Create AJAX request
            const xhr = new XMLHttpRequest();
            
            // Progress handler
            if (progressBarInner) {
                xhr.upload.addEventListener('progress', function(e) {
                    if (e.lengthComputable) {
                        const percentComplete = Math.round((e.loaded / e.total) * 100);
                        progressBarInner.style.width = percentComplete + '%';
                        progressBarInner.textContent = percentComplete + '%';
                    }
                });
            }
            
            // Load completed handler
            xhr.addEventListener('load', function() {
                if (xhr.status >= 200 && xhr.status < 300) {
                    window.location.href = xhr.responseURL;
                } else {
                    if (progressBar) {
                        progressBar.classList.add('d-none');
                    }
                    showAlert('Error uploading file: ' + xhr.statusText, 'danger');
                }
            });
            
            // Error handler
            xhr.addEventListener('error', function() {
                if (progressBar) {
                    progressBar.classList.add('d-none');
                }
                showAlert('Network error occurred during upload', 'danger');
            });
            
            // Abort handler
            xhr.addEventListener('abort', function() {
                if (progressBar) {
                    progressBar.classList.add('d-none');
                }
                showAlert('Upload aborted', 'warning');
            });
            
            // Send the form data
            xhr.open('POST', uploadForm.action);
            xhr.send(formData);
        });
    }
}

/**
 * Initialize subtitle editor functionality
 */
function initSubtitleEditor() {
    const fontSizeRange = document.getElementById('fontSizeRange');
    const fontSizeValue = document.getElementById('fontSizeValue');
    const fontColor = document.getElementById('fontColor');
    const fontColorPicker = document.getElementById('fontColorPicker');
    const fontColorPreview = document.getElementById('fontColorPreview');
    const bgColor = document.getElementById('bgColor');
    const bgColorPicker = document.getElementById('bgColorPicker');
    const bgColorPreview = document.getElementById('bgColorPreview');
    const subtitleWidth = document.getElementById('subtitleWidth');
    const widthValue = document.getElementById('widthValue');
    const position = document.getElementById('position');
    const saveButton = document.getElementById('saveSubtitles');
    const generateBtn = document.getElementById('generateBtn');
    const detectLanguageBtn = document.getElementById('detectLanguageBtn');
    const translateBtns = document.querySelectorAll('.translate-btn');
    const subtitlePreview = document.getElementById('subtitlePreview');
    const previewText = document.getElementById('previewText');
    const customPosX = document.getElementById('customPosX');
    const customPosY = document.getElementById('customPosY');
    
    // Add event listeners to prevent line breaks in subtitle text fields
    const addLineBreakListeners = () => {
        const subtitleTextInputs = document.querySelectorAll('.subtitle-text');
        subtitleTextInputs.forEach(input => {
            // Remove existing event listener to avoid duplicates
            input.removeEventListener('input', handleLineBreakRemoval);
            // Add event listener
            input.addEventListener('input', handleLineBreakRemoval);
        });
    };
    
    // Function to handle line break removal
    const handleLineBreakRemoval = (event) => {
        const input = event.target;
        // If the input contains line breaks, remove them
        if (input.value.includes('\n') || input.value.includes('\r')) {
            const cursorPosition = input.selectionStart;
            // Replace line breaks with spaces
            const newValue = input.value.replace(/\n/g, ' ').replace(/\r/g, '');
            input.value = newValue;
            // Try to keep cursor position
            try {
                input.setSelectionRange(cursorPosition, cursorPosition);
            } catch (e) {
                // Ignore errors with selection range
            }
        }
    };
    
    // Initial setup of line break listeners
    addLineBreakListeners();
    
    // Setup a mutation observer to watch for changes to the subtitle table
    const subtitleTable = document.getElementById('subtitlesTable');
    if (subtitleTable) {
        const observer = new MutationObserver(() => {
            // When the table changes, reapply the line break listeners
            addLineBreakListeners();
        });
        
        observer.observe(subtitleTable, { 
            childList: true, 
            subtree: true 
        });
    }
    
    // Try to initialize the modal if it exists
    let processingModal = null;
    const modalElement = document.getElementById('processingModal');
    if (modalElement && typeof bootstrap !== 'undefined') {
        try {
            processingModal = new bootstrap.Modal(modalElement);
        } catch (e) {
            console.warn('Could not initialize processing modal:', e);
        }
    }
    
    // Auto-translate to Brazilian Portuguese if available
    // Find the pt-br translate button and trigger it automatically
    const autoPtBrBtn = document.querySelector('.translate-btn[data-lang="pt-br"]');
    if (autoPtBrBtn) {
        // We'll add a small delay to make sure the page is fully loaded
        setTimeout(() => {
            // Skip the confirmation dialog for pt-br translation
            const targetLanguage = autoPtBrBtn.dataset.lang;
            
            // Get the detected language first
            fetch('/detect_language', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const detectedLanguage = data.language_code;
                    
                    // Only translate if not already pt-br
                    if (detectedLanguage !== 'pt-br' && detectedLanguage !== 'pt') {
                        showAlert(`Detectamos que o vídeo está em ${data.language_name}. Traduzindo para Português Brasileiro...`, 'info');
                        
                        // Perform the translation
                        fetch('/translate_subtitles', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                target_language: targetLanguage
                            })
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                // Update the subtitle table with translated text
                                updateSubtitleTable(data.subtitles);
                                showAlert('Legendas traduzidas para Português Brasileiro com sucesso!', 'success');
                            }
                        })
                        .catch(error => {
                            console.error('Error translating subtitles:', error);
                        });
                    } else {
                        showAlert('O vídeo já está em Português!', 'info');
                    }
                }
            })
            .catch(error => {
                console.error('Error detecting language:', error);
            });
        }, 1000);
    }
    
    // Update font size display
    if (fontSizeRange && fontSizeValue) {
        fontSizeRange.addEventListener('input', function() {
            fontSizeValue.textContent = this.value;
        });
    }
    
    // Save subtitles
    if (saveButton) {
        saveButton.addEventListener('click', function() {
            const rows = document.querySelectorAll('#subtitlesTable tbody tr');
            const subtitles = [];
            
            if (!rows.length) {
                showAlert('No subtitles found to save', 'warning');
                return;
            }
            
            rows.forEach(row => {
                const index = parseInt(row.dataset.index);
                const startTime = row.querySelector('.start-time').value;
                const endTime = row.querySelector('.end-time').value;
                let text = row.querySelector('.subtitle-text').value;
                
                // Ensure there are no line breaks in the text - replace with spaces
                text = text.replace(/\n/g, ' ').replace(/\r/g, '');
                
                // Also update the input field to reflect the changes
                row.querySelector('.subtitle-text').value = text;
                
                subtitles.push({
                    index: index,
                    start: startTime,
                    end: endTime,
                    text: text
                });
            });
            
            // Send subtitles data to server
            fetch('/save_subtitles', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(subtitles)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('Subtitles saved successfully!', 'success');
                } else {
                    showAlert('Error saving subtitles: ' + data.error, 'danger');
                }
            })
            .catch(error => {
                showAlert('Error: ' + error, 'danger');
            });
        });
    }
    
    // Detect subtitle language
    if (detectLanguageBtn) {
        detectLanguageBtn.addEventListener('click', function(e) {
            e.preventDefault();
            showAlert('Detecting language...', 'info');
            
            fetch('/detect_language', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert(`Detected language: ${data.language_name} (${data.language_code})`, 'success');
                } else {
                    showAlert('Error detecting language: ' + data.error, 'danger');
                }
            })
            .catch(error => {
                showAlert('Error detecting language: ' + error, 'danger');
            });
        });
    }
    
    // Translate subtitles
    if (translateBtns.length > 0) {
        translateBtns.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                
                const targetLanguage = this.dataset.lang;
                const targetLanguageName = this.textContent;
                
                // Confirm translation
                if (!confirm(`Are you sure you want to translate the subtitles to ${targetLanguageName}?`)) {
                    return;
                }
                
                showAlert(`Translating subtitles to ${targetLanguageName}...`, 'info');
                
                fetch('/translate_subtitles', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        target_language: targetLanguage
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Update the subtitle table with translated text
                        updateSubtitleTable(data.subtitles);
                        showAlert(`Subtitles translated to ${targetLanguageName} successfully!`, 'success');
                    } else {
                        showAlert('Error translating subtitles: ' + data.error, 'danger');
                    }
                })
                .catch(error => {
                    showAlert('Error translating subtitles: ' + error, 'danger');
                });
            });
        });
    }
    
    // Initialize the subtitle preview
    if (subtitlePreview && previewText) {
        // Sample subtitle texts for preview
        const sampleTexts = [
            "Exemplo de legenda em português",
            "Este é um teste de legenda em uma linha",
            "Arraste para posicionar as legendas"
        ];
        
        // Randomly select a sample text
        previewText.textContent = sampleTexts[Math.floor(Math.random() * sampleTexts.length)];
        
        // Setup draggable functionality
        makeDraggable(subtitlePreview);
        
        // Update preview based on form controls
        if (fontSizeRange) {
            fontSizeRange.addEventListener('input', updateSubtitlePreview);
        }
        
        if (fontColor) {
            fontColor.addEventListener('change', updateSubtitlePreview);
        }
        
        if (fontColorPicker) {
            fontColorPicker.addEventListener('input', function() {
                // When color picker changes, update the preview directly with the hex value
                if (fontColorPreview) {
                    fontColorPreview.style.backgroundColor = this.value;
                }
                if (subtitlePreview) {
                    subtitlePreview.style.color = this.value;
                }
                
                // Also add a custom option to the select if it doesn't exist
                const customOption = document.querySelector('#fontColor option[value="custom"]');
                if (!customOption) {
                    const option = document.createElement('option');
                    option.value = 'custom';
                    option.textContent = 'Custom';
                    fontColor.appendChild(option);
                }
                fontColor.value = 'custom';
            });
        }
        
        if (bgColor) {
            bgColor.addEventListener('change', updateSubtitlePreview);
        }
        
        if (bgColorPicker) {
            bgColorPicker.addEventListener('input', function() {
                // When color picker changes, update the preview directly with the hex value
                if (bgColorPreview) {
                    bgColorPreview.style.backgroundColor = this.value;
                }
                if (subtitlePreview) {
                    subtitlePreview.style.backgroundColor = this.value;
                }
                
                // Also add a custom option to the select if it doesn't exist
                const customOption = document.querySelector('#bgColor option[value="custom"]');
                if (!customOption) {
                    const option = document.createElement('option');
                    option.value = 'custom';
                    option.textContent = 'Custom';
                    bgColor.appendChild(option);
                }
                bgColor.value = 'custom';
            });
        }
        
        if (subtitleWidth) {
            subtitleWidth.addEventListener('input', function() {
                if (widthValue) {
                    widthValue.textContent = this.value;
                }
                if (subtitlePreview) {
                    subtitlePreview.style.width = this.value + '%';
                    subtitlePreview.style.left = ((100 - this.value) / 2) + '%';
                }
            });
        }
        
        if (position) {
            position.addEventListener('change', function() {
                const pos = this.value;
                if (pos === 'custom') {
                    // Do nothing, keep the current dragged position
                    return;
                }
                
                // Set predefined positions
                if (subtitlePreview) {
                    switch(pos) {
                        case 'bottom':
                            subtitlePreview.style.bottom = '10%';
                            subtitlePreview.style.top = 'auto';
                            subtitlePreview.style.left = ((100 - parseInt(subtitleWidth?.value || 80)) / 2) + '%';
                            break;
                        case 'top':
                            subtitlePreview.style.top = '10%';
                            subtitlePreview.style.bottom = 'auto';
                            subtitlePreview.style.left = ((100 - parseInt(subtitleWidth?.value || 80)) / 2) + '%';
                            break;
                        case 'center':
                            subtitlePreview.style.top = '50%';
                            subtitlePreview.style.bottom = 'auto';
                            subtitlePreview.style.transform = 'translateY(-50%)';
                            subtitlePreview.style.left = ((100 - parseInt(subtitleWidth?.value || 80)) / 2) + '%';
                            break;
                    }
                    
                    // Update hidden position inputs
                    updatePositionInputs();
                }
            });
        }
        
        // Initial preview update
        updateSubtitlePreview();
    }
    
    // Show processing modal when generating video
    if (generateBtn) {
        const form = document.getElementById('subtitleOptionsForm');
        if (form) {
            form.addEventListener('submit', function() {
                // Show the modal if available
                if (processingModal) {
                    processingModal.show();
                } else {
                    console.log('Processing video, please wait...');
                }
            });
        }
    }
    
    // Helper function to make an element draggable
    function makeDraggable(element) {
        if (!element) return;
        
        let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
        let isDragging = false;
        
        // Mouse events for desktop
        element.onmousedown = dragMouseDown;
        
        // Touch events for mobile
        element.addEventListener('touchstart', dragTouchStart, { passive: false });
        
        function dragMouseDown(e) {
            e.preventDefault();
            // Get the mouse cursor position at startup
            pos3 = e.clientX;
            pos4 = e.clientY;
            isDragging = true;
            
            document.onmouseup = closeDragElement;
            document.onmousemove = elementDrag;
            
            // Set position to custom
            if (position) {
                position.value = 'custom';
            }
        }
        
        function dragTouchStart(e) {
            e.preventDefault();
            if (e.touches.length === 1) {
                // Get the touch position at startup
                pos3 = e.touches[0].clientX;
                pos4 = e.touches[0].clientY;
                isDragging = true;
                
                document.addEventListener('touchend', closeTouchDragElement, { passive: false });
                document.addEventListener('touchcancel', closeTouchDragElement, { passive: false });
                document.addEventListener('touchmove', elementTouchDrag, { passive: false });
                
                // Set position to custom
                if (position) {
                    position.value = 'custom';
                }
            }
        }
        
        function elementDrag(e) {
            if (!isDragging) return;
            
            e.preventDefault();
            // Calculate the new cursor position
            pos1 = pos3 - e.clientX;
            pos2 = pos4 - e.clientY;
            pos3 = e.clientX;
            pos4 = e.clientY;
            
            // Set the element's new position (bound to container)
            const containerRect = element.parentElement.getBoundingClientRect();
            const elementRect = element.getBoundingClientRect();
            
            // Calculate new position with bounds checking
            let newLeft = elementRect.left - pos1 - containerRect.left;
            let newTop = elementRect.top - pos2 - containerRect.top;
            
            // Ensure the element stays within the container
            newLeft = Math.max(0, Math.min(newLeft, containerRect.width - elementRect.width));
            newTop = Math.max(0, Math.min(newTop, containerRect.height - elementRect.height));
            
            // Apply new position
            element.style.left = newLeft + 'px';
            element.style.top = newTop + 'px';
            element.style.bottom = 'auto';
            element.style.transform = 'none';
            
            // Update position inputs
            updatePositionInputs();
        }
        
        function elementTouchDrag(e) {
            if (!isDragging || e.touches.length !== 1) return;
            
            e.preventDefault();
            // Calculate the new touch position
            pos1 = pos3 - e.touches[0].clientX;
            pos2 = pos4 - e.touches[0].clientY;
            pos3 = e.touches[0].clientX;
            pos4 = e.touches[0].clientY;
            
            // Set the element's new position (bound to container)
            const containerRect = element.parentElement.getBoundingClientRect();
            const elementRect = element.getBoundingClientRect();
            
            // Calculate new position with bounds checking
            let newLeft = elementRect.left - pos1 - containerRect.left;
            let newTop = elementRect.top - pos2 - containerRect.top;
            
            // Ensure the element stays within the container
            newLeft = Math.max(0, Math.min(newLeft, containerRect.width - elementRect.width));
            newTop = Math.max(0, Math.min(newTop, containerRect.height - elementRect.height));
            
            // Apply new position
            element.style.left = newLeft + 'px';
            element.style.top = newTop + 'px';
            element.style.bottom = 'auto';
            element.style.transform = 'none';
            
            // Update position inputs
            updatePositionInputs();
        }
        
        function closeDragElement() {
            // Stop moving when mouse button is released
            document.onmouseup = null;
            document.onmousemove = null;
            isDragging = false;
        }
        
        function closeTouchDragElement() {
            // Stop moving when touch ends
            document.removeEventListener('touchend', closeTouchDragElement);
            document.removeEventListener('touchcancel', closeTouchDragElement);
            document.removeEventListener('touchmove', elementTouchDrag);
            isDragging = false;
        }
    }
    
    // Helper function to update the subtitle preview
    function updateSubtitlePreview() {
        if (!subtitlePreview) return;
        
        // Update font size
        if (fontSizeRange) {
            subtitlePreview.style.fontSize = fontSizeRange.value + 'px';
        }
        
        // Update font color
        if (fontColor) {
            subtitlePreview.style.color = fontColor.value;
            if (fontColorPreview) {
                fontColorPreview.style.backgroundColor = fontColor.value;
            }
            if (fontColorPicker && fontColor.value !== 'custom') {
                fontColorPicker.value = convertNamedColorToHex(fontColor.value);
            }
        }
        
        // Update background color
        if (bgColor) {
            const bgColorValue = bgColor.value === 'transparent' ? 'rgba(0,0,0,0.5)' : bgColor.value;
            subtitlePreview.style.backgroundColor = bgColorValue;
            if (bgColorPreview) {
                bgColorPreview.style.backgroundColor = bgColorValue;
            }
            if (bgColorPicker && bgColor.value !== 'custom' && bgColor.value !== 'transparent') {
                bgColorPicker.value = convertNamedColorToHex(bgColor.value);
            }
        }
        
        // Update width
        if (subtitleWidth) {
            subtitlePreview.style.width = subtitleWidth.value + '%';
            subtitlePreview.style.left = ((100 - parseInt(subtitleWidth.value)) / 2) + '%';
        }
        
        // Update position inputs
        updatePositionInputs();
    }
    
    // Helper function to update the position inputs
    function updatePositionInputs() {
        if (!subtitlePreview || !customPosX || !customPosY) return;
        
        const containerRect = subtitlePreview.parentElement.getBoundingClientRect();
        const elementRect = subtitlePreview.getBoundingClientRect();
        
        // Calculate position as percentages
        let posX = ((elementRect.left - containerRect.left) / containerRect.width) * 100;
        let posY = ((elementRect.top - containerRect.top) / containerRect.height) * 100;
        
        // Update the hidden inputs
        customPosX.value = Math.round(posX);
        customPosY.value = Math.round(posY);
    }
    
    // Helper function to convert named colors to hex
    function convertNamedColorToHex(colorName) {
        // Create a temporary element to compute the color
        const temp = document.createElement('div');
        temp.style.color = colorName;
        document.body.appendChild(temp);
        const computedColor = getComputedStyle(temp).color;
        document.body.removeChild(temp);
        
        // Parse the computed RGB value
        const rgb = computedColor.match(/\d+/g);
        if (rgb && rgb.length >= 3) {
            return '#' + 
                parseInt(rgb[0]).toString(16).padStart(2, '0') +
                parseInt(rgb[1]).toString(16).padStart(2, '0') +
                parseInt(rgb[2]).toString(16).padStart(2, '0');
        }
        
        return '#ffffff';  // Default to white if conversion fails
    }
}

/**
 * Update subtitle table with new subtitle data
 */
function updateSubtitleTable(subtitles) {
    if (!subtitles || !subtitles.length) return;
    
    const tbody = document.querySelector('#subtitlesTable tbody');
    if (!tbody) return;
    
    // Clear existing rows
    tbody.innerHTML = '';
    
    // Add new rows
    subtitles.forEach(subtitle => {
        const row = document.createElement('tr');
        row.dataset.index = subtitle.index;
        
        // Ensure text has no line breaks
        const text = subtitle.text ? subtitle.text.replace(/\n/g, ' ').replace(/\r/g, '') : '';
        
        row.innerHTML = `
            <td>${subtitle.index}</td>
            <td>
                <input type="text" class="form-control form-control-sm start-time" 
                       value="${subtitle.start}" pattern="\\d{2}:\\d{2}:\\d{2},\\d{3}">
            </td>
            <td>
                <input type="text" class="form-control form-control-sm end-time" 
                       value="${subtitle.end}" pattern="\\d{2}:\\d{2}:\\d{2},\\d{3}">
            </td>
            <td>
                <input type="text" class="form-control form-control-sm subtitle-text" 
                       value="${text}">
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

/**
 * Helper function to format file size in human-readable format
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Helper function to show alert messages
 */
function showAlert(message, type = 'info') {
    // Create alert element
    const alertEl = document.createElement('div');
    alertEl.className = `alert alert-${type} alert-dismissible fade show`;
    alertEl.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Try to find the main content container
    const mainContent = document.querySelector('main.container');
    if (mainContent) {
        mainContent.insertBefore(alertEl, mainContent.firstChild);
        
        // Auto dismiss after 5 seconds if bootstrap is available
        setTimeout(() => {
            try {
                if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
                    const bsAlert = new bootstrap.Alert(alertEl);
                    bsAlert.close();
                } else {
                    // Fallback if bootstrap Alert is not available
                    alertEl.remove();
                }
            } catch (e) {
                console.warn('Error auto-dismissing alert:', e);
                // Fallback removal
                if (alertEl.parentNode) {
                    alertEl.parentNode.removeChild(alertEl);
                }
            }
        }, 5000);
    } else {
        // Fallback if main container not found - append to body
        console.warn('Main container not found for alert, appending to body');
        document.body.appendChild(alertEl);
    }
}
