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
