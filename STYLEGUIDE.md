# STYLEGUIDE - Hệ thống thiết kế PO System

Tài liệu mô tả hệ thống thiết kế UI/UX thống nhất cho PO System, áp dụng cho giao diện chạy trên Replit. Mục tiêu: hiện đại, trực quan, hiệu năng tốt, dễ bảo trì, tiệm cận WCAG 2.1 AA, không thay đổi nền tảng hay luồng chạy.

## Nguyên tắc
- Nhất quán: token màu, typography, spacing, corner radius, elevation.
- Rõ ràng: nội dung tiếng Việt, ngắn gọn, dễ hiểu, tránh thuật ngữ khó.
- A11y: focus rõ, aria đầy đủ, điều hướng bàn phím, tương phản đạt chuẩn.
- Hiệu năng: hạn chế reflow, debounce/throttle, reduced motion khi cần.
- Mô-đun: CSS tiện lợi, JS không xâm lấn, có thể mở rộng.

## Design Tokens

Màu chủ đạo (chế độ sáng):
- Primary: #667eea
- Secondary: #764ba2
- Success: #11998e → #38ef7d (gradient)
- Danger: #eb3349 → #f45c43 (gradient)
- Info: #45b7d1
- Surface: #ffffff → #f8fafc
- Text: #1e293b

Màu chủ đạo (chế độ tối):
- Background: #1a1a2e → #16213e
- Surface: #2a2a3e
- Text: #e0e0e0
- Border: #3a3a4e

Corner radius:
- Nhỏ: 8px
- Trung bình: 12px
- Lớn: 16px–24px (card, container)

Elevation (đổ bóng gợi ý, giảm trên mobile):
- Nhẹ: 0 4px 15px rgba(0,0,0,.1)
- Vừa: 0 12px 24px rgba(0,0,0,.12)
- Mạnh: 0 32px 64px rgba(0,0,0,.2)

Spacing (scale 4):
- 4, 8, 12, 16, 20, 24, 32, 40, 48

Typography:
- Font: Poppins (UI), Space Grotesk (tiêu đề), Inter (fallback)
- Body: 16px/1.6
- H1: 2.5–4rem (responsive)
- H2: 1.75–2rem
- H3: 1.25–1.5rem
- Label/Meta: 0.85–1rem, đậm vừa

## Breakpoints (tham chiếu Bootstrap 5)
- xs <576px, sm ≥576px, md ≥768px, lg ≥992px, xl ≥1200px
- Quy tắc: nội dung quan trọng hiển thị trước; giảm chuyển động, bóng trên xs/sm.

## Thành phần (Components)

Buttons
- .btn-primary: nền gradient primary, không viền, hover nâng nhẹ.
- .btn-success/.btn-danger: dùng gradient đã quy ước.
- .btn-custom: border-radius 16px, hiệu ứng shimmer nhẹ khi hover.
- Trạng thái loading: thêm .loading (CSS pseudo ::after spinner).
- Accessibility: có aria-label cho nút icon-only.

Inputs
- .form-control/.form-select: focus border-color #667eea, shadow 0 0 0 0.2rem rgba(102,126,234,.25)
- Nền sáng trong, tránh shadow nặng liên tục.

Cards
- .product-card, .stats-card: surface sáng, border tinh tế, backdrop-filter nhẹ.
- Hover: dịch -2px tới -12px tùy loại; giảm trên prefers-reduced-motion.

Toasts
- Container: .toast-container (aria-live="polite", aria-atomic="true")
- Item: .toast-notification + biến thể .toast-success/.toast-error/.toast-warning/.toast-info
- Đóng: .toast-close có aria-label, icon x.

Overlays
- .progress-overlay + .progress-content, có progress-bar, progress-text.
- Dùng .show để bật/tắt (opacity transition).

Empty/Skeleton
- .empty-state cho danh sách trống, có icon, CTA “Xóa tìm kiếm”.
- .product-card.loading/.stats-card.loading có shimmer-loading.

Taskbar
- Chứa thời gian, username, nút dark-mode-toggle, logout.
- Nút dark-mode-toggle đổi icon moon/sun theo trạng thái.

## Dark Mode
- Body bật class .dark-mode.
- Nền, text, border, surface theo token chế độ tối.
- Toggle bằng JS [JavaScript.toggleDarkMode()](web/static/enhancements.js:1) và lưu localStorage.
- Ưu tiên system: nếu chưa lưu, theo prefers-color-scheme.

## Accessibility (WCAG 2.1 AA)
- Skip link: .visually-hidden-focusable trước Taskbar, href="#mainContent".
- Landmark: role="main" cho vùng nội dung chính.
- Focus: :focus-visible outline 3px, offset 2px; tương phản đạt chuẩn.
- Phím tắt: Ctrl/Cmd + K (tập trung ô tìm kiếm), Ctrl/Cmd + D (dark mode).
- Thông báo: aria-live cho toast; autosave indicator không gây che khuất nội dung.

## Motion (chuyển động)
- Tôn trọng @media (prefers-reduced-motion: reduce).
- Tắt hoặc giảm: backgroundFloat, containerFloat, shimmer, pulse.
- Tránh animation nặng trên nhiều phần tử đồng thời; ưu tiên transform thay vì layout.

## Iconography
- FontAwesome 6 (CDN) theo cấu hình hiện có.
- Icon phải đi kèm label văn bản hoặc aria-label rõ ràng.

## Copy (ngôn ngữ)
- Sử dụng tiếng Việt chuẩn, nhất quán; tránh từ mơ hồ.
- Nút hành động: động từ ở đầu (“Xóa tìm kiếm”, “Đăng xuất”, “Làm mới”).
- Thông điệp lỗi: ngắn gọn, có hướng xử lý.

## JS Guidelines
- Không gắn sự kiện inline phức tạp; nếu cần, dùng hàm ngắn (ví dụ searchProductsDebounced()).
- Debounce các thao tác gõ/tìm kiếm: 200–300ms.
- Tránh thao tác DOM lặp; dùng batch cập nhật, limit reflow.
- Dọn listener khi không dùng; tránh memory leak.

## CSS Guidelines
- Gom class theo khối chức năng (buttons, forms, cards, overlays).
- Không lạm dụng !important; dùng specificity tối thiểu.
- Tận dụng biến thể .dark-mode .selector cho chế độ tối.
- Tôn trọng breakpoints; giảm bóng/hiệu ứng trên màn hình nhỏ.

## Tokens → Class mapping (mẫu)
- Primary actions → .btn-primary, .btn-primary-custom
- Info surfaces → .alert-custom, .search-sort-card
- Emphasis text → .stats-number, .header h1

## Ví dụ sử dụng

Toast
```html
<button class="btn btn-primary" onclick="showToast('Đã lưu cấu hình', 'success')">Hiển thị toast</button>
```

Empty state
```html
<div id="empty-state" class="empty-state" role="status" aria-live="polite" style="display:none">
  <div class="empty-icon"><i class="fas fa-box-open"></i></div>
  <h5>Không có sản phẩm phù hợp</h5>
  <button class="btn btn-outline-primary btn-sm" onclick="clearSearch()">Xóa tìm kiếm</button>
</div>
```

Skeleton
```html
<div class="product-card loading">...</div>
```

## Liên hệ
- Cập nhật/thêm token mới: mở PR kèm lý do và ảnh chụp màn hình trước/sau.
- Tồn tại xung đột style: ưu tiên enhancements.css; hạn chế thay đổi inline style trong template.

## Phạm vi không thay đổi
- Không thay đổi cấu hình Replit (.replit, replit.nix), lệnh run hay đường dẫn URL/API hiện hành.
- Không thêm build tool hoặc dịch vụ ngoài.

## Kế hoạch mở rộng
- Tách dần CSS inline trong template sang enhancements.css theo module.
- Thêm component “Banner thông báo” và “Stepper tiến trình” nếu phát sinh nhu cầu.
- Tích hợp theme màu tùy biến qua CSS variables (an toàn, tùy chọn).