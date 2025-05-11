/* 
 * Skrypt automatycznie zamykający alerty
 * Ten skrypt automatycznie zamyka wszystkie alerty Bootstrap (z wyjątkiem alertów typu danger)
 * po określonym czasie
 */

document.addEventListener('DOMContentLoaded', function() {
    // Function to dismiss alerts
    function setupAlertDismiss() {
        // Auto-dismiss all non-danger alerts after 5 seconds
        const alerts = document.querySelectorAll('.alert:not(.alert-danger)');
        
        alerts.forEach(function(alert) {
            // Set timeout to close the alert
            setTimeout(function() {
                // Fade out the alert
                alert.style.transition = 'opacity 0.5s ease';
                alert.style.opacity = '0';
                
                // Remove from DOM after animation completes
                setTimeout(function() {
                    // If the alert is still in the DOM, remove it
                    if (alert.parentNode) {
                        alert.parentNode.removeChild(alert);
                    }
                }, 500);
            }, 5000);
        });
    }
    
    // Initialize alert dismissal when page loads
    setupAlertDismiss();
    
    // Also set up a mutation observer to handle dynamically added alerts
    const messagesContainer = document.querySelector('.messages');
    
    if (messagesContainer) {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    setupAlertDismiss();
                }
            });
        });
        
        observer.observe(messagesContainer, { childList: true });
    }
});
