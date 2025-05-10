// Force browser to clear CSS cache
(function() {
    console.log("Running cache clearing script...");
    
    // Get all stylesheets
    const stylesheets = Array.from(document.styleSheets);
    
    // Log which stylesheets are loaded
    console.log("Currently loaded stylesheets:");
    stylesheets.forEach((sheet, index) => {
        try {
            console.log(`[${index}] ${sheet.href}`);
        } catch (e) {
            console.log(`[${index}] Unable to access stylesheet info`);
        }
    });
    
    // Attempt to reload main stylesheet with cache busting
    function reloadStylesheet(href) {
        const newHref = href.split('?')[0] + '?v=' + new Date().getTime();
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = newHref;
        document.head.appendChild(link);
        console.log(`Reloaded stylesheet: ${newHref}`);
        
        // Attempt to remove old stylesheet after loading
        link.onload = function() {
            const oldLinks = document.querySelectorAll('link[href*="style.css"]');
            if (oldLinks.length > 1) {
                oldLinks[0].remove();
                console.log("Removed old stylesheet");
            }
        };
    }
    
    // Find and reload main stylesheet
    const mainStylesheet = stylesheets.find(sheet => {
        try {
            return sheet.href && sheet.href.includes('style.css');
        } catch {
            return false;
        }
    });
    
    if (mainStylesheet && mainStylesheet.href) {
        console.log(`Main stylesheet found: ${mainStylesheet.href}`);
        reloadStylesheet(mainStylesheet.href);
    } else {
        console.log("Main stylesheet not found in document");
    }
    
    // Set a flag in localStorage to indicate the cache has been cleared
    localStorage.setItem('kspCacheCleared', new Date().toISOString());
    console.log("Cache clearing completed");
})();
