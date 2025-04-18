// UI Enhancement Scripts for TechHub

// Dark mode functionality
function initDarkMode() {
  const darkModeToggle = document.getElementById('darkModeToggle');
  
  // Check for saved preference
  const prefersDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const savedMode = localStorage.getItem('darkMode');
  
  // Apply dark mode based on saved preference or system preference
  if (savedMode === 'true' || (savedMode === null && prefersDarkMode)) {
    document.body.classList.add('dark-mode');
  }
  
  // Toggle dark mode when the button is clicked
  if (darkModeToggle) {
    darkModeToggle.addEventListener('click', () => {
      document.body.classList.toggle('dark-mode');
      
      // Save preference to localStorage
      const isDarkMode = document.body.classList.contains('dark-mode');
      localStorage.setItem('darkMode', isDarkMode);
    });
  }
}

// Animation on scroll
document.addEventListener('DOMContentLoaded', function() {
  // Initialize dark mode
  initDarkMode();
  
  // Add animation classes to elements as they scroll into view
  const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  // Observe all elements with the 'animate-on-scroll' class
  document.querySelectorAll('.animate-on-scroll').forEach(element => {
    observer.observe(element);
  });

  // Apply ripple effect to buttons
  const buttons = document.querySelectorAll('.btn-enhanced');
  buttons.forEach(button => {
    button.addEventListener('click', function(e) {
      const x = e.clientX - e.target.getBoundingClientRect().left;
      const y = e.clientY - e.target.getBoundingClientRect().top;

      const ripple = document.createElement('span');
      ripple.classList.add('ripple-effect');
      ripple.style.left = `${x}px`;
      ripple.style.top = `${y}px`;

      this.appendChild(ripple);

      setTimeout(() => {
        ripple.remove();
      }, 600);
    });
  });

  // Enhanced dropdown behavior
  const dropdowns = document.querySelectorAll('.dropdown-toggle');
  dropdowns.forEach(dropdown => {
    dropdown.addEventListener('click', function() {
      const dropdownMenu = this.nextElementSibling;
      
      // Toggle active class
      this.classList.toggle('active');
      
      // Toggle visibility
      if (dropdownMenu.style.maxHeight) {
        dropdownMenu.style.maxHeight = null;
        dropdownMenu.style.opacity = '0';
        
        setTimeout(() => {
          dropdownMenu.style.display = 'none';
        }, 200);
      } else {
        dropdownMenu.style.display = 'block';
        
        setTimeout(() => {
          dropdownMenu.style.maxHeight = dropdownMenu.scrollHeight + 'px';
          dropdownMenu.style.opacity = '1';
        }, 10);
      }
    });
  });

  // Add smooth scroll behavior for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      e.preventDefault();
      const targetId = this.getAttribute('href');
      
      if (targetId === '#') return;
      
      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        window.scrollTo({
          top: targetElement.offsetTop - 80, // Adjust for fixed header
          behavior: 'smooth'
        });
      }
    });
  });

  // Add hover effect for cards
  const cards = document.querySelectorAll('.enhanced-card');
  cards.forEach(card => {
    card.addEventListener('mouseenter', function() {
      this.style.transform = 'translateY(-5px)';
      this.style.boxShadow = 'var(--shadow-md)';
    });
    
    card.addEventListener('mouseleave', function() {
      this.style.transform = 'translateY(0)';
      this.style.boxShadow = 'var(--shadow-sm)';
    });
  });

  // Enhance form inputs with focus effects
  const formInputs = document.querySelectorAll('input, textarea, select');
  formInputs.forEach(input => {
    const formGroup = input.closest('.form-group') || input.parentElement;
    
    input.addEventListener('focus', function() {
      formGroup.classList.add('focused');
    });
    
    input.addEventListener('blur', function() {
      formGroup.classList.remove('focused');
      
      if (this.value) {
        formGroup.classList.add('has-value');
      } else {
        formGroup.classList.remove('has-value');
      }
    });
    
    // Initial state
    if (input.value) {
      formGroup.classList.add('has-value');
    }
  });

  // Mobile menu toggle
  const mobileMenuButton = document.querySelector('.mobile-menu-button');
  if (mobileMenuButton) {
    const mobileMenu = document.querySelector('.mobile-menu');
    
    mobileMenuButton.addEventListener('click', function() {
      this.classList.toggle('active');
      
      if (mobileMenu.classList.contains('active')) {
        mobileMenu.classList.remove('active');
        
        setTimeout(() => {
          mobileMenu.style.display = 'none';
        }, 300);
      } else {
        mobileMenu.style.display = 'block';
        
        setTimeout(() => {
          mobileMenu.classList.add('active');
        }, 10);
      }
    });
  }
});

// Add parallax effect to hero sections
window.addEventListener('scroll', function() {
  const parallaxElements = document.querySelectorAll('.parallax');
  
  parallaxElements.forEach(element => {
    const scrollPosition = window.pageYOffset;
    const speed = element.dataset.speed || 0.5;
    
    element.style.transform = `translateY(${scrollPosition * speed}px)`;
  });
}); 