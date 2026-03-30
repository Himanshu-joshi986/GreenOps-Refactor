// ========================================
// Global Utilities & Helper Functions
// ========================================

/**
 * Format large numbers with commas
 */
function formatNumber(num) {
    if (typeof num !== 'number') return '0';
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Calculate color based on score
 */
function getScoreColor(score) {
    if (score >= 80) return '#10b981'; // Green
    else if (score >= 60) return '#f59e0b'; // Amber
    else if (score >= 40) return '#ef4444'; // Red
    return '#dc2626'; // Dark red
}

/**
 * Get score interpretation text
 */
function getScoreInterpretation(score) {
    if (score >= 80) return 'Excellent - Well Optimized';
    else if (score >= 60) return 'Good - Minor Improvements Possible';
    else if (score >= 40) return 'Fair - Room for Optimization';
    return 'Needs Work - Significant Optimizations Available';
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0 shadow-lg" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body fw-600">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = toastContainer.lastElementChild;
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', () => {
        if (toastElement.parentElement) {
            toastElement.remove();
        }
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.style.cssText = `
        position: fixed;
        top: 1.5rem;
        right: 1.5rem;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        gap: 1rem;
        max-width: 400px;
    `;
    document.body.appendChild(container);
    return container;
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Validate code input
 */
function validateCode(code) {
    if (!code || code.length < 20) {
        showToast('Code must be at least 20 characters', 'danger');
        return false;
    }
    if (code.length > 10000) {
        showToast('Code cannot exceed 10,000 characters', 'danger');
        return false;
    }
    return true;
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy:', err);
        showToast('Failed to copy', 'danger');
    });
}

/**
 * Format bytes to human readable
 */
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Smooth scroll to element
 */
function smoothScroll(selector) {
    const element = document.querySelector(selector);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

/**
 * API call helper
 */
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(endpoint, options);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP Error: ${response.status}`);
        }
        
        const responseData = await response.json();
        return responseData;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ========================================
// Page Initialization
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    initializeTooltips();
    setupEventListeners();
    setupScrollAnimation();
    initializeAnalysisForm();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                smoothScroll(href);
            }
        });
    });
}

/**
 * Setup scroll animations
 */
function setupScrollAnimation() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });
    
    document.querySelectorAll('.card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'all 0.3s ease-out';
        observer.observe(card);
    });
}

// ========================================
// Analysis Form Handler
// ========================================

function initializeAnalysisForm() {
    const form = document.getElementById('analysisForm');
    if (!form) return;
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const code = formData.get('code').trim();
        const hardware = formData.get('hardware') || 'x86';
        const carbon = formData.get('carbon_intensity') || '450';
        const latency = formData.get('latency') || '50';
        const region = formData.get('region') || 'us-east-1';
        
        // Validate code
        if (!validateCode(code)) {
            return;
        }
        
        // Show loading state
        const submitButton = form.querySelector('button[type="submit"]');
        const originalButtonText = submitButton.innerHTML;
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Analyzing...';
        
        try {
            // Send to API
            const response = await apiCall('/api/analyze', 'POST', {
                code: code,
                hardware: hardware,
                carbon_intensity: parseFloat(carbon),
                latency_ms: parseFloat(latency),
                region: region
            });
            
            if (response && response.green_score !== undefined) {
                // Store result for results page
                sessionStorage.setItem('analysisResult', JSON.stringify(response));
                sessionStorage.setItem('analysisCode', code);
                
                // Redirect to results page
                window.location.href = '/result';
            } else {
                throw new Error('Unexpected response format from server');
            }
            
        } catch (error) {
            console.error('Analysis error:', error);
            showToast(`Failed to analyze: ${error.message}`, 'danger');
        } finally {
            // Restore button
            submitButton.disabled = false;
            submitButton.innerHTML = originalButtonText;
        }
    });
    
    // Update character count
    const codeInput = document.getElementById('codeInput');
    if (codeInput) {
        codeInput.addEventListener('input', function() {
            const charCount = document.getElementById('charCount');
            if (charCount) {
                charCount.textContent = this.value.length;
            }
        });
    }
    
    // Update slider displays
    const carbonSlider = document.getElementById('carbonIntensitySlider');
    if (carbonSlider) {
        carbonSlider.addEventListener('input', function() {
            const display = document.getElementById('carbonIntensityDisplay');
            if (display) display.textContent = this.value;
            document.querySelector('input[name="carbon_intensity"]').value = this.value;
        });
    }
    
    const latencySlider = document.getElementById('latencySlider');
    if (latencySlider) {
        latencySlider.addEventListener('input', function() {
            const display = document.getElementById('latencyDisplay');
            if (display) display.textContent = this.value;
            document.querySelector('input[name="latency"]').value = this.value;
        });
    }
}

// ========================================
// Result Download & Export
// ========================================

function downloadResults() {
    const result = window.analysisResult;
    if (!result) {
        showToast('No analysis results available', 'warning');
        return;
    }
    
    const csv = 'Metric,Value\n' +
        `Green Score,${result.green_score}/100\n` +
        `Energy Consumption,${result.predicted_energy_kwh} kWh\n` +
        `Carbon Emissions,${result.carbon_grams} grams CO2\n` +
        `Hardware Type,${result.context_used.hardware}\n` +
        `Carbon Intensity,${result.context_used.carbon_intensity} g/kWh\n` +
        `Latency SLA,${result.context_used.latency_ms}ms\n` +
        `Region,${result.context_used.region}\n` +
        `Lines of Code,${result.code_metrics.lines_of_code}\n` +
        `Code Complexity,${result.code_metrics.complexity_score}\n` +
        `Recommendation,"${result.suggested_refactor}"\n`;
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `greenops-analysis-${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
    
    showToast('Report downloaded successfully!', 'success');
}

function shareResults() {
    const result = window.analysisResult;
    if (!result) {
        showToast('No analysis results to share', 'warning');
        return;
    }
    
    const text = `Green Code Analysis Report\n` +
        `Green Score: ${result.green_score}/100\n` +
        `Energy: ${result.predicted_energy_kwh.toFixed(6)} kWh\n` +
        `Carbon Impact: ${result.carbon_grams.toFixed(2)}g CO2\n` +
        `Suggestion: ${result.suggested_refactor}`;
    
    if (navigator.share) {
        navigator.share({
            title: 'GreenOps Code Analysis',
            text: text
        }).catch(err => console.log('Share failed:', err));
    } else {
        copyToClipboard(text);
        showToast('Results copied to clipboard for sharing', 'info');
    }
}
