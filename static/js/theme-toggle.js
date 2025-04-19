/**
 * Unified theme toggle functionality for LearnHub
 * This script handles dark/light mode preferences consistently across the site
 */

function initThemeToggle() {
    // Get all toggle buttons from the page
    const themeToggles = document.querySelectorAll('#themeToggle, #themeToggleMobile');
    const darkModeToggle = document.getElementById('darkModeToggle'); // For backward compatibility
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Helper function to set theme
    function setTheme(isDark) {
        // Apply to html element for better theme transitioning
        document.documentElement.classList.toggle('dark-mode', isDark);
        // Keep body class for backward compatibility
        document.body.classList.toggle('dark-mode', isDark);
        
        // Update icons on all theme toggles
        const icon = isDark ? '<i class="fas fa-sun" aria-hidden="true"></i>' : '<i class="fas fa-moon" aria-hidden="true"></i>';
        
        themeToggles.forEach(toggle => {
            if (toggle) toggle.innerHTML = icon;
        });
        
        if (darkModeToggle) darkModeToggle.innerHTML = icon;
        
        // Save preference to localStorage for immediate access on subsequent pages
        localStorage.setItem('dark-mode', isDark ? 'true' : 'false');
        
        // If we're in a context with server-side session storage
        if (typeof setDarkModeUrl !== 'undefined') {
            // Save preference to server
            fetch(setDarkModeUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ dark_mode: isDark })
            }).catch(error => console.error('Error saving theme preference:', error));
        }
    }
    
    // Check stored preference first
    const storedTheme = localStorage.getItem('dark-mode');
    if (storedTheme !== null) {
        const isDark = storedTheme === 'true';
        setTheme(isDark);
    } else if (prefersDarkScheme.matches && 
              !document.documentElement.classList.contains('dark-mode') && 
              !document.body.classList.contains('dark-mode')) {
        // If no stored preference, check system preference
        setTheme(true);
    }
    
    // Toggle theme on click for all theme toggles
    themeToggles.forEach(toggle => {
        if (toggle) {
            toggle.addEventListener('click', function() {
                const isDark = !document.documentElement.classList.contains('dark-mode');
                setTheme(isDark);
            });
        }
    });
    
    // For backward compatibility
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', function() {
            const isDark = !document.documentElement.classList.contains('dark-mode');
            setTheme(isDark);
        });
    }
    
    // Listen for system preference changes
    prefersDarkScheme.addEventListener('change', function(e) {
        const storedTheme = localStorage.getItem('dark-mode');
        if (storedTheme === null) {
            // Only apply system preference if user hasn't set a preference
            setTheme(e.matches);
        }
    });
    
    // Add preload class to body on page load and remove it after a delay
    // to prevent transitions from firing when page loads
    document.body.classList.add('preload');
    setTimeout(() => {
        document.body.classList.remove('preload');
    }, 300);
}

// Initialize as soon as the DOM is loaded
document.addEventListener('DOMContentLoaded', initThemeToggle); 