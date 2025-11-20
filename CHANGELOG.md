# CHANGELOG

Tóm tắt thay đổi theo phiên bản.

## 2025-11-09 — Nâng cấp UI/UX & Hiệu năng (không đổi nền tảng Replit)

Phạm vi: Hiện đại hóa giao diện, cải thiện A11y, tối ưu hiệu năng phía client, dọn code dư; giữ nguyên cấu hình, lệnh run, API, URL, và hành vi cốt lõi.

Added
- Dark mode + nút chuyển theme trên Taskbar; tự động theo prefers-color-scheme; lưu trạng thái bằng localStorage.
- A11y: Skip link tới nội dung chính; role="main"; :focus-visible nổi bật; aria-live cho toast; cải thiện mô tả nút.
- Empty state cho lưới sản phẩm khi không có kết quả.
- Skeleton/loading state nhẹ cho product-card và stats-card.
- Debounce tìm kiếm (300ms) theo sự kiện input để giảm reflow/repaint.
- Reduced motion: tắt/giảm animation nặng khi người dùng chọn giảm chuyển động.

Changed
- Chuẩn hóa hệ thống toast: tạo .toast-container, .toast-notification theo CSS; loại bỏ inline style JS.
- Hợp nhất autosave indicator về một id #saveIndicator, tạo động khi thiếu; điều khiển icon/trạng thái bằng JS.
- Cập nhật taskbar: thêm nút chuyển dark/light; đồng bộ icon theo trạng thái theme.
- Tinh chỉnh cập nhật hiển thị sản phẩm: đếm visibleCount để bật/tắt empty state.

Removed
- Xóa div #saveIndicator trùng lặp ở cuối trang index.
- Xóa khối autosave indicator inline và style phụ thừa trong enhancements_head.

Files impacted
- web/static/enhancements.js — Toast chuẩn hóa, autosave indicator hợp nhất, toggle dark mode, debounce tìm kiếm, progress overlay theo CSS.
- web/templates/index.html — Skip link, role="main", nút dark mode, đổi onkeyup → oninput, thêm empty state, cập nhật updateProductVisibility, setSkeleton, xóa duplicate #saveIndicator.
- web/static/enhancements.css — Focus-visible, skip-link, reduced motion, empty state, skeleton, style cho dark-mode toggle.
- web/templates/enhancements_head.html — Chỉ include assets; bỏ div #saveIndicator và style nội bộ không cần thiết.
- README.md — Bổ sung mục nâng cấp, liên kết tới STYLEGUIDE, TESTING, PERFORMANCE, CHANGELOG.

Tương thích & Migration
- Không thay đổi API server hay schema dữ liệu.
- Không chỉnh sửa .replit, replit.nix, Procfile, lệnh run hoặc cơ chế khởi chạy.
- Không bổ sung phụ thuộc runtime; JS/CSS vẫn chạy thuần trên trình duyệt.

Hướng dẫn kiểm tra nhanh
- Mở trang chủ (/): xác nhận Taskbar hiển thị nút chuyển theme.
- Nhập nhanh vào ô tìm kiếm: UI không giật lag; empty state xuất hiện khi không có kết quả.
- Dùng phím: Ctrl/Cmd + K (focus ô tìm kiếm), Ctrl/Cmd + D (chuyển theme).
- Bật giảm chuyển động (OS): animation nền và card giảm rõ rệt.

Gợi ý rollback
- Sao lưu branch hiện tại; nếu cần rollback, revert các file liệt kê ở "Files impacted" về commit trước 2025-11-09.