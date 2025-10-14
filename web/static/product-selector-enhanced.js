/**
 * Product Selector Enhanced - Advanced product selection features
 * Phase 1: Enhanced UI for product selection
 */

// View mode toggle
let currentViewMode = localStorage.getItem('viewMode') || 'grid';

function setViewMode(mode) {
    currentViewMode = mode;
    localStorage.setItem('viewMode', mode);
    
    const productGrid = document.querySelector('.product-grid');
    if (productGrid) {
        productGrid.className = `product-grid view-${mode}`;
    }
    
    // Update active button
    document.querySelectorAll('.view-toggle button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-view="${mode}"]`)?.classList.add('active');
}

// Category filter
function filterByCategory(category) {
    const productCards = document.querySelectorAll('.product-card');
    
    productCards.forEach(card => {
        const productCategory = card.dataset.category;
        if (category === 'all' || productCategory === category) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// Favorites system
let favorites = JSON.parse(localStorage.getItem('favorites') || '[]');

function toggleFavorite(productId) {
    const index = favorites.indexOf(productId);
    
    if (index > -1) {
        favorites.splice(index, 1);
    } else {
        favorites.push(productId);
    }
    
    localStorage.setItem('favorites', JSON.stringify(favorites));
    updateFavoriteUI(productId);
}

function updateFavoriteUI(productId) {
    const favoriteBtn = document.querySelector(`[data-product="${productId}"] .favorite-btn`);
    if (favoriteBtn) {
        if (favorites.includes(productId)) {
            favoriteBtn.classList.add('active');
            favoriteBtn.innerHTML = '<i class="fas fa-star"></i>';
        } else {
            favoriteBtn.classList.remove('active');
            favoriteBtn.innerHTML = '<i class="far fa-star"></i>';
        }
    }
}

function showFavoritesOnly() {
    const productCards = document.querySelectorAll('.product-card');
    
    productCards.forEach(card => {
        const productId = card.dataset.product;
        if (favorites.includes(productId)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// Recent products
let recentProducts = JSON.parse(localStorage.getItem('recentProducts') || '[]');

function addToRecent(productId) {
    // Remove if already exists
    const index = recentProducts.indexOf(productId);
    if (index > -1) {
        recentProducts.splice(index, 1);
    }
    
    // Add to beginning
    recentProducts.unshift(productId);
    
    // Keep only last 10
    recentProducts = recentProducts.slice(0, 10);
    
    localStorage.setItem('recentProducts', JSON.stringify(recentProducts));
}

function showRecentOnly() {
    const productCards = document.querySelectorAll('.product-card');
    
    productCards.forEach(card => {
        const productId = card.dataset.product;
        if (recentProducts.includes(productId)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// Quick jump modal
function showQuickJump() {
    const modal = document.getElementById('quickJumpModal');
    if (modal) {
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Focus on search input
        setTimeout(() => {
            const input = modal.querySelector('input');
            if (input) input.focus();
        }, 300);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Set initial view mode
    setViewMode(currentViewMode);
    
    // Initialize favorites UI
    favorites.forEach(productId => {
        updateFavoriteUI(productId);
    });
    
    // Quick jump keyboard shortcut (Ctrl/Cmd + J)
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'j') {
            e.preventDefault();
            showQuickJump();
        }
    });
});

console.log('Product Selector Enhanced loaded successfully');
