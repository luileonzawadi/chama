// Mobile responsiveness for modern features

document.addEventListener('DOMContentLoaded', function() {
    // Mobile sidebar toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
    }
    
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
    }
    
    // Close sidebar when clicking outside
    document.addEventListener('click', function(event) {
        if (sidebar && sidebar.classList.contains('show') && 
            !sidebar.contains(event.target) && 
            event.target !== sidebarToggle &&
            event.target !== mobileMenuToggle) {
            sidebar.classList.remove('show');
        }
    });
    
    // Responsive tables
    const tables = document.querySelectorAll('table');
    tables.forEach(table => {
        if (!table.parentElement.classList.contains('table-responsive')) {
            const wrapper = document.createElement('div');
            wrapper.classList.add('table-responsive');
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        }
    });
    
    // Make cards touch-friendly
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.classList.add('mobile-friendly');
    });
    
    // Adjust QR code size on mobile
    const qrCode = document.getElementById('qrcode');
    if (qrCode && window.innerWidth < 768) {
        const canvas = qrCode.querySelector('canvas');
        if (canvas) {
            canvas.style.width = '150px';
            canvas.style.height = '150px';
        }
    }
    
    // Add swipe gestures for mobile
    let touchStartX = 0;
    let touchEndX = 0;
    
    document.addEventListener('touchstart', e => {
        touchStartX = e.changedTouches[0].screenX;
    });
    
    document.addEventListener('touchend', e => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    });
    
    function handleSwipe() {
        if (touchEndX < touchStartX - 100 && sidebar) {
            // Swipe left - hide sidebar
            sidebar.classList.remove('show');
        }
        
        if (touchEndX > touchStartX + 100 && sidebar) {
            // Swipe right - show sidebar
            sidebar.classList.add('show');
        }
    }
});