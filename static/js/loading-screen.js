/* Loading screen functions */

// Global variables for the loading screen
let loadingInterval;
let progressValue = 0;
let isIndeterminate = false;

// Initialize loading screen handling on page load
document.addEventListener('DOMContentLoaded', function() {
    // Add event listener for beforeunload to prevent hiding the loading screen when the page is being unloaded
    window.addEventListener('beforeunload', function() {
        // Set a flag in sessionStorage to indicate we're navigating away intentionally
        sessionStorage.setItem('intentionalNavigation', 'true');
    });
    
    // Check if we're coming from another page with loading screen already shown
    if (sessionStorage.getItem('loadingScreenActive') === 'true') {
        // If loading screen was active, keep it on
        const message = sessionStorage.getItem('loadingMessage') || 'Ładowanie...';
        const showProgress = sessionStorage.getItem('showProgress') === 'true';
        window.showLoading(message, showProgress);
        
        // Set initial progress
        window.updateLoadingProgress(20);
        
        // Clean up sessionStorage
        sessionStorage.removeItem('loadingScreenActive');
        sessionStorage.removeItem('loadingMessage');
        sessionStorage.removeItem('showProgress');
    }
});

/**
 * Show the loading overlay with a progress bar
 * @param {string} message - The message to display
 * @param {boolean} showProgress - Whether to show a progress bar (default: false for indeterminate loading)
 */
window.showLoading = function(message = 'Ładowanie...', showProgress = false) {
    // Get overlay elements
    const overlay = document.getElementById('loading-overlay');
    const text = overlay.querySelector('.loading-text');
    const progressBar = document.getElementById('loading-progress-bar');
    const progressContainer = overlay.querySelector('.progress-container');
    
    // Set message
    text.textContent = message;
    
    // Reset progress
    progressValue = 0;
    isIndeterminate = !showProgress;
    
    // Show/hide progress bar based on mode
    if (showProgress) {
        progressContainer.style.display = 'block';
        updateProgressBar(0);
    } else {
        // For indeterminate loading, we still show the progress bar but make it move automatically
        progressContainer.style.display = 'block';
        progressBar.classList.add('progress-bar-animated', 'progress-bar-striped');
        updateProgressBar(0);
        
        // Start automatic progress simulation for indeterminate loading
        clearInterval(loadingInterval);
        loadingInterval = setInterval(function() {
            // Slowly increase progress, but never reach 100%
            if (progressValue < 90) {
                progressValue += Math.random() * (2 - 0.1) + 0.1; // Random increment between 0.1 and 2
                updateProgressBar(progressValue);
            }
        }, 200);
    }
    
    // Show overlay
    overlay.classList.add('active');
};

/**
 * Navigate to a URL with loading screen
 * @param {string} url - The URL to navigate to
 * @param {string} message - The loading message to display
 * @param {boolean} showProgress - Whether to show a progress bar
 */
window.navigateWithLoading = function(url, message = 'Przygotowywanie listy przedmiotów...', showProgress = true) {
    // Store loading state in session storage so it persists across page navigation
    sessionStorage.setItem('loadingScreenActive', 'true');
    sessionStorage.setItem('loadingMessage', message);
    sessionStorage.setItem('showProgress', showProgress);
    
    // Show loading screen
    window.showLoading(message, showProgress);
    
    // Allow the loading overlay to render before navigating
    setTimeout(function() {
        window.location.href = url;
    }, 50); // Short delay to ensure loading screen is shown
    
    return false; // Prevent default anchor behavior
};

/**
 * Update the progress bar value
 * @param {number} value - Progress value (0-100)
 */
window.updateLoadingProgress = function(value) {
    if (isIndeterminate) {
        clearInterval(loadingInterval);
        isIndeterminate = false;
    }
    
    progressValue = Math.min(Math.max(value, 0), 100); // Ensure value is between 0-100
    updateProgressBar(progressValue);
    
    // If progress reaches 100%, hide the loading screen after a short delay
    if (progressValue >= 100) {
        setTimeout(window.hideLoading, 500);
    }
};

/**
 * Hide the loading overlay
 */
window.hideLoading = function() {
    const overlay = document.getElementById('loading-overlay');
    clearInterval(loadingInterval);
    overlay.classList.remove('active');
};

/**
 * Internal function to update the progress bar UI
 * @param {number} value - Progress value (0-100)
 */
function updateProgressBar(value) {
    const progressBar = document.getElementById('loading-progress-bar');
    const roundedValue = Math.round(value);
    
    progressBar.style.width = roundedValue + '%';
    progressBar.setAttribute('aria-valuenow', roundedValue);
    progressBar.textContent = roundedValue + '%';
}
