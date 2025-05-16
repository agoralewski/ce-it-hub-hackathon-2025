/* Debug script for Select2 focus issues */
(function() {
    // Wait for DOM to be fully loaded
    document.addEventListener('DOMContentLoaded', function() {
        if (window.jQuery) {
            // Log when any Select2 dropdown is opened
            $(document).on('select2:open', function(e) {
                console.log('Select2 opened:', e.target);
                
                // Check if search field exists
                setTimeout(function() {
                    var searchField = document.querySelector('.select2-container--open .select2-search__field');
                    console.log('Search field found:', searchField);
                    
                    if (searchField) {
                        console.log('Search field active element before focus:', document.activeElement);
                        searchField.focus();
                        console.log('Search field active element after focus:', document.activeElement);
                        
                        // Add visual indicator that the field has focus
                        searchField.style.border = '2px solid #d0242c';
                    }
                }, 10);
            });
            
            console.log('Select2 debug script loaded successfully');
        } else {
            console.error('jQuery not loaded, Select2 debug script not initialized');
        }
    });
})();
