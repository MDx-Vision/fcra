// Tab switching (for single-page navigation if needed)
function switchTab(tabId, element) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // Remove active from all nav tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });

    // Show selected tab
    const targetTab = document.getElementById(tabId);
    if (targetTab) {
        targetTab.classList.add('active');
    }

    // Set active nav
    if (element) {
        element.classList.add('active');
    }

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Re-run animations for this tab
    setTimeout(() => {
        initAnimations();
        initStatusDropdowns();
    }, 100);
}

// Status dropdown color change
function updateStatusColor(select) {
    const value = select.value;
    select.style.fontWeight = '600';
    if (value === 'FROZEN') {
        select.style.background = '#0d9488';
        select.style.color = 'white';
        select.style.borderColor = '#0d9488';
    } else if (value === 'NOT FROZEN') {
        select.style.background = 'rgba(220, 38, 38, 0.15)';
        select.style.color = '#dc2626';
        select.style.borderColor = '#dc2626';
    } else {
        // PENDING - amber/yellow
        select.style.background = 'rgba(245, 158, 11, 0.15)';
        select.style.color = '#d97706';
        select.style.borderColor = '#f59e0b';
    }
}

// Initialize status dropdowns
function initStatusDropdowns() {
    document.querySelectorAll('#status select, .status-select').forEach(select => {
        // Set initial color
        updateStatusColor(select);
        // Add change listener
        select.addEventListener('change', function() {
            updateStatusColor(this);
        });
    });
}

// Animated numbers
function animateNumber(element) {
    const target = parseInt(element.dataset.value, 10);
    const prefix = element.dataset.prefix || '';
    const duration = 1500;
    const start = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 4);
        const current = Math.round(eased * target);
        element.textContent = prefix + current.toLocaleString();

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

// Progress ring
function animateProgressRing() {
    const circle = document.querySelector('.progress-ring-circle');
    const percentText = document.querySelector('.progress-percent-text');
    const progressBar = document.querySelector('.progress-bar-fill');

    if (!circle) return;

    const target = parseInt(circle.dataset.progress, 10);
    const circumference = 471.24;
    const duration = 1400;

    setTimeout(() => {
        const start = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 4);
            const currentPercent = Math.round(eased * target);
            const offset = circumference - (currentPercent / 100) * circumference;

            circle.style.strokeDashoffset = offset;
            if (percentText) percentText.textContent = currentPercent;

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }

        requestAnimationFrame(update);
    }, 600);

    // Progress bar
    if (progressBar) {
        setTimeout(() => {
            progressBar.style.width = progressBar.dataset.width + '%';
        }, 600);
    }
}

// Initialize animations
function initAnimations() {
    // Animate numbers
    document.querySelectorAll('.animate-number').forEach(el => {
        el.textContent = el.dataset.prefix || '0';
        animateNumber(el);
    });

    // Progress ring
    animateProgressRing();
}

// Run on load
document.addEventListener('DOMContentLoaded', function() {
    initAnimations();
    initStatusDropdowns();
});
