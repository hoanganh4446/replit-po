# 🎨 Design System Guide - PO Hub Website

## Tổng Quan

Tài liệu này mô tả toàn bộ hệ thống thiết kế được áp dụng cho website PO Hub, dựa trên các tiêu chuẩn từ `sample.html` và các best practices thiết kế hiện đại.

---

## 📋 Mục Lục

1. [Color Palette](#color-palette)
2. [Typography](#typography)
3. [Spacing & Layout](#spacing--layout)
4. [Components](#components)
5. [Responsive Design](#responsive-design)
6. [Accessibility](#accessibility)

---

## 🎯 Color Palette

### Primary Colors
```css
--background-color: #000000       /* Nền chính - đen */
--card-background: #111111        /* Nền card - đen đậm */
--border-color: #222222           /* Màu border - xám đen */
--text-color: #ffffff             /* Text chính - trắng */
--text-color-secondary: #aaaaaa   /* Text phụ - xám nhạt */
--primary-color: #ffffff          /* Màu chính CTA - trắng */
--primary-text-color: #000000     /* Text trên primary - đen */
```

### Accent Colors
```css
--sale-color: #ff4d4d             /* Khuyến mãi - đỏ */
--rating-color: #fdd835           /* Rating - vàng */
--success-color: #10b981          /* Thành công - xanh */
--warning-color: #fbbf24          /* Cảnh báo - cam */
--danger-color: #f87171           /* Lỗi - đỏ */
--info-color: #3b82f6             /* Thông tin - xanh dương */
```

### Design Pattern
- **Dark Theme**: Nền đen với text trắng để tạo cảm giác hiện đại, chuyên nghiệp
- **High Contrast**: Đảm bảo độ tương phản cao (WCAG AAA)
- **Subtle Borders**: Sử dụng màu border nhẹ nhàng để phân chia các phần tử

---

## 🔤 Typography

### Font Family
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
```

### Font Sizes (Responsive Scale)
```css
--font-size-xs: 0.75rem    /* 12px */
--font-size-sm: 0.875rem   /* 14px */
--font-size-md: 1rem       /* 16px */
--font-size-lg: 1.125rem   /* 18px */
--font-size-xl: 1.25rem    /* 20px */
--font-size-2xl: 1.5rem    /* 24px */
--font-size-3xl: 2rem      /* 32px */
```

### Font Weights
```css
--font-weight-normal: 400
--font-weight-medium: 500
--font-weight-semibold: 600
--font-weight-bold: 700
```

### Heading Hierarchy
- **H1**: 2rem (32px), semibold, used for main page titles
- **H2**: 1.5rem (24px), semibold, used for section titles
- **H3**: 1.25rem (20px), semibold, used for subsections
- **H4**: 1.125rem (18px), semibold, used for component titles
- **Body**: 1rem (16px), normal, line-height: 1.6
- **Small**: 0.875rem (14px), normal, for secondary text

---

## 📏 Spacing & Layout

### Spacing Scale
```css
--spacing-xs: 0.25rem    /* 4px */
--spacing-sm: 0.5rem     /* 8px */
--spacing-md: 1rem       /* 16px */
--spacing-lg: 1.5rem     /* 24px */
--spacing-xl: 2rem       /* 32px */
--spacing-2xl: 3rem      /* 48px */
```

### Border Radius (Rounded Corners)
```css
--radius-sm: 4px
--radius-md: 8px
--radius-lg: 12px
--radius-xl: 16px
--radius-2xl: 20px
--radius-full: 999px     /* Fully rounded (pill-shaped) */
```

### Container & Grid
- **Max Width**: 1200px
- **Padding**: 1.5rem (24px) on each side
- **Gap**: 1.5rem between grid items
- **Grid Columns**: 
  - Desktop: 4 columns
  - Tablet (992px): 3 columns
  - Mobile (768px): 2 columns
  - Small Mobile (480px): 1 column

---

## 🧩 Components

### Header
```html
<!-- Structure -->
<header class="header">
  <div class="container header-container">
    <div class="header-logo">Logo/Brand</div>
    <nav class="header-nav"><!-- Navigation links --></nav>
    <div class="header-actions"><!-- Buttons --></div>
  </div>
</header>
```

**Styling**:
- Background: `--background-color` (#000000)
- Border Bottom: 1px solid `--border-color`
- Padding: `--spacing-md` vertical
- Sticky positioning
- Z-index: 100

### Footer
```html
<!-- Structure -->
<footer class="footer">
  <div class="container footer-container">
    <div class="footer-col"><!-- Column 1 --></div>
    <div class="footer-col links"><!-- Links column --></div>
    <!-- More columns -->
  </div>
  <div class="container footer-bottom"><!-- Copyright --></div>
</footer>
```

**Styling**:
- Background: #050505 (darker than main background)
- Border Top: 1px solid `--border-color`
- Padding: 3rem top, 2rem bottom
- Grid: 4 columns on desktop, responsive on smaller screens

### Product Card
```html
<div class="product-card">
  <span class="sale-badge">-30%</span>
  <div class="product-icon-container">
    <img src="..." class="product-icon" />
  </div>
  <h3 class="product-name">Product Name</h3>
  <div class="product-rating">★★★★★</div>
  <div class="product-price">
    <span class="current-price">Price</span>
    <span class="old-price">Old Price</span>
  </div>
  <button class="add-to-cart-btn">Add to Cart</button>
</div>
```

**Styling**:
- Background: `--card-background`
- Border: 1px solid `--border-color`
- Border Radius: 12px
- Padding: 1rem
- Hover: translateY(-5px), box-shadow
- Transition: 0.2s ease

### Filter Tags
```html
<div class="product-filters">
  <button class="filter-tag active">Filter 1</button>
  <button class="filter-tag">Filter 2</button>
</div>
```

**Styling**:
- Background: `--card-background`
- Color: `--text-color-secondary`
- Border: 1px solid `--border-color`
- Padding: 0.5rem 0.75rem
- Border Radius: 20px (pill-shaped)
- Hover/Active: background-color #222

### Buttons
```css
/* Primary Button */
.btn-primary {
  background-color: #ffffff;
  color: #000000;
  padding: 0.5rem 1rem;
  border-radius: 6px;
}

/* Secondary Button */
.btn-secondary {
  background-color: #111111;
  color: #ffffff;
  border: 1px solid #222222;
  padding: 0.5rem 1rem;
  border-radius: 6px;
}

/* Hover State */
.btn:hover {
  transform: translateY(-2px);
  opacity: 0.9;
}
```

---

## 📱 Responsive Design

### Breakpoints
```css
/* Large Desktop */
@media (min-width: 1200px) {
  /* 4-column grid, full sidebar visible */
}

/* Desktop */
@media (max-width: 992px) {
  .product-grid { grid-template-columns: repeat(3, 1fr); }
  .footer-container { grid-template-columns: repeat(2, 1fr); }
}

/* Tablet */
@media (max-width: 768px) {
  .header-nav { display: none; }
  .product-grid { grid-template-columns: repeat(2, 1fr); }
  .footer-container { grid-template-columns: 1fr; }
  .container { padding: 0 1rem; }
}

/* Mobile */
@media (max-width: 480px) {
  .product-grid { grid-template-columns: 1fr; }
  .footer-container { grid-template-columns: 1fr; }
  .header-container { flex-direction: column; }
}
```

### Responsive Strategy
1. **Mobile First**: Start with mobile styles, then enhance for larger screens
2. **Flexible Layouts**: Use CSS Grid and Flexbox for fluid responsiveness
3. **Touch-Friendly**: Minimum touch target size: 44x44px
4. **Performance**: Optimize images and use appropriate sizes

---

## ♿ Accessibility

### Color Contrast
- **WCAG AAA**: Minimum 7:1 contrast ratio for normal text
- **WCAG AA**: Minimum 4.5:1 contrast ratio for normal text
- **Dark Theme**: #ffffff on #000000 = 21:1 (excellent contrast)

### Focus States
```css
:focus-visible {
  outline: 2px solid #ffffff;
  outline-offset: 2px;
}
```

### Keyboard Navigation
- All interactive elements must be keyboard accessible
- Tab order should follow logical visual flow
- Use `aria-label` for icon-only buttons

### Semantic HTML
```html
<!-- Use semantic tags -->
<header></header>
<nav></nav>
<main></main>
<footer></footer>
<article></article>
<section></section>

<!-- Use proper heading hierarchy -->
<h1>Main Title</h1>
<h2>Section Title</h2>
<h3>Subsection</h3>
```

### ARIA Attributes
```html
<button aria-label="Close menu">✕</button>
<div role="status" aria-live="polite">Status message</div>
<a href="#mainContent" class="skip-link">Skip to main content</a>
```

### Reduced Motion Support
```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.001ms !important;
    transition-duration: 0.001ms !important;
  }
}
```

---

## 🎬 Animations & Transitions

### Transition Durations
```css
--transition-fast: 0.15s ease
--transition-base: 0.2s ease
--transition-smooth: 0.3s ease
```

### Common Animations
```css
/* Hover lift effect */
transform: translateY(-2px);
box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);

/* Fade in */
animation: fadeIn 0.3s ease;

/* Smooth scroll */
scroll-behavior: smooth;
```

---

## 📦 CSS File Organization

### File Structure
```
web/static/
├── design-system.css              /* Core design tokens & utilities */
├── app.css                        /* Main app layout & components */
├── header-footer-enhanced.css     /* Header/footer specific styles */
├── enhancements.css               /* Phase 1 enhancements */
└── product-selector-enhanced.css  /* Product selector styles */
```

### Loading Order (Important!)
1. `design-system.css` - Base variables and utilities
2. `header-footer-enhanced.css` - Header/footer overrides
3. `enhancements.css` - Enhancement styles
4. `product-selector-enhanced.css` - Product selector
5. `app.css` - Main app styles (should be last to allow overrides)

---

## 🔄 Implementation Checklist

- [x] Color palette applied consistently
- [x] Typography hierarchy established
- [x] Spacing scale implemented
- [x] Border radius applied uniformly
- [x] Responsive breakpoints configured
- [x] Header/footer updated
- [x] Dark theme support
- [x] Accessibility standards met (WCAG AA)
- [x] Transitions and animations configured
- [x] Mobile-first approach
- [x] Touch-friendly targets (44x44px minimum)
- [x] Keyboard navigation support
- [x] Focus states visible
- [x] Semantic HTML usage
- [x] Performance optimizations

---

## 🎓 Usage Examples

### Creating a New Card Component
```html
<div class="glass-card">
  <h3>Card Title</h3>
  <p class="text-secondary">Card description</p>
  <button class="btn btn-primary">Action</button>
</div>
```

### Spacing Between Elements
```html
<div class="mb-3"><!-- margin-bottom: 1rem -->
  <h2>Section Title</h2>
</div>
<div class="p-4"><!-- padding: 2rem -->
  Content here
</div>
```

### Responsive Grid
```html
<div class="product-grid">
  <!-- Auto-responsive: 4 cols on desktop, 2 on tablet, 1 on mobile -->
  <div class="product-card">...</div>
  <div class="product-card">...</div>
</div>
```

---

## 📞 Support & Questions

For questions about the design system:
1. Check this guide first
2. Review the relevant CSS file (design-system.css, app.css, etc.)
3. Look at sample.html for reference implementations
4. Check existing component implementations in the codebase

---

## 📅 Last Updated
- **Date**: 2025-11-15
- **Version**: 1.0
- **Reference**: sample.html design standards
- **Author**: Design System Team
