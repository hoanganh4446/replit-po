# TESTING - Hướng dẫn kiểm thử PO System

Mục tiêu: đảm bảo chức năng cốt lõi, UI/UX, A11y, hiệu năng cơ bản hoạt động ổn định trên Replit mà không đổi nền tảng.

Phạm vi:
- Trang chủ [/](web/templates/index.html)
- API sản phẩm [/api/products](src/managers/api_manager.py)
- Chuyển theme dark/light [JavaScript.toggleDarkMode()](web/static/enhancements.js:1)
- Tìm kiếm và sắp xếp sản phẩm [HTML.index](web/templates/index.html)
- Toast và autosave indicator [CSS.enhancements](web/static/enhancements.css) / [JavaScript.enhancements()](web/static/enhancements.js:1)

Yêu cầu nền tảng:
- Không cần cài thêm thư viện kiểm thử; dùng Python tiêu chuẩn và trình duyệt.

1) Kiểm thử khói (Smoke test) thủ công
- Mở ứng dụng trên Replit, truy cập trang chủ [/](web/templates/index.html).
- Xác nhận Taskbar hiển thị thời gian và username.
- Bấm nút chuyển theme: icon đổi moon/sun; trang đổi giao diện; trạng thái lưu lại sau refresh.
- Nhập vào ô tìm kiếm: kết quả lọc theo từ khóa; empty state hiện khi không có kết quả.
- Bấm “Làm mới”: loading spinner hiển thị; lưới sản phẩm cập nhật.

2) Kiểm thử A11y nhanh (WCAG 2.1 AA tiệm cận)
- Phím tắt: Ctrl/Cmd + K tập trung ô tìm kiếm; Ctrl/Cmd + D chuyển theme.
- Dùng Tab/Shift+Tab: focus-visible outline rõ, không bị trap.
- Skip link: nhấn Tab ở đầu trang hiển thị “Bỏ qua điều hướng…”, Enter nhảy tới [role="main"](web/templates/index.html:837).
- Toast: aria-live="polite", không che nội dung quan trọng.

3) Kiểm thử API cơ bản
- Từ trình duyệt DevTools hoặc curl:
  - GET /api/products trả JSON danh sách sản phẩm (có các khóa name, type, template_exists).

4) Kiểm thử hiệu năng định tính
- Bật “prefers-reduced-motion” ở hệ điều hành: kiểm tra chuyển động giảm đáng kể.
- Gõ nhanh vào ô tìm kiếm: UI không giật lag do [searchProductsDebounced()](web/static/enhancements.js:1).

5) Kiểm thử lỗi & thông báo
- Ngắt mạng tạm thời rồi thực hiện loadProducts(): thông báo lỗi trên console, UI không crash.
- Export với bộ lọc không hợp lệ: hệ thống hiển thị thông báo lỗi ngắn gọn, không rò rỉ thông tin nhạy cảm.

6) Kiểm thử bảo mật đầu vào (cơ bản)
- Nhập ký tự đặc biệt vào ô tìm kiếm; xác nhận không có XSS phản chiếu trên UI.
- Kiểm tra các form modal (nếu có) không chấp nhận input trống khi bắt buộc.

7) Kiểm thử tự động (tùy chọn)
- Chạy script smoke tự động bằng Python (sẽ được cung cấp): [tests/basic_smoke_test.py](tests/basic_smoke_test.py)
- Script sử dụng Flask test client để xác nhận:
  - Trang chủ trả về HTTP 200
  - API /api/products trả JSON hợp lệ (dict và có ít nhất 1 sản phẩm)

Cách chạy script tự động (sau khi tạo file):
```bash
python tests/basic_smoke_test.py
```

8) Checklist sau nâng cấp
- Không thay đổi .replit, replit.nix, lệnh run, URL, API cốt lõi.
- UI responsive trên desktop/tablet/mobile.
- Dark mode hoạt động và lưu trạng thái.
- A11y cơ bản đạt: skip link, focus-visible, aria-live.
- Tìm kiếm debounce hoạt động, empty/skeleton state hiển thị đúng.

9) Báo cáo kết quả kiểm thử
- Ghi nhận kết quả, ảnh chụp màn hình, và vấn đề còn lại trong CHANGELOG.

10) Lỗi thường gặp & cách xử lý
- 404 /api/products: kiểm tra route server và dữ liệu sản phẩm.
- Lỗi CSS không áp dụng toast: kiểm tra class .toast-container, .toast-notification có mặt trên DOM.

Tài liệu liên quan
- [README.md](README.md)
- [CHANGELOG.md](CHANGELOG.md)
- [STYLEGUIDE.md](STYLEGUIDE.md)
- [PERFORMANCE.md](PERFORMANCE.md)

Ghi chú
- Không thêm phụ thuộc ngoài; mọi kiểm thử dùng công cụ có sẵn.
- Nếu cần mở rộng test, ưu tiên tạo script Python thuần và không chạm vào lệnh run trên Replit.