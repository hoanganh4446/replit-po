# PERFORMANCE - Báo cáo và hướng dẫn đo hiệu năng

Mục tiêu
- Cải thiện cảm nhận tải trang đầu tiên (TTFP), FCP, LCP và TTI trên môi trường Replit mà không thay đổi nền tảng hoặc build tool.
- Giảm reflow/repaint không cần thiết, tôn trọng tùy chọn reduced motion của người dùng, và giữ trải nghiệm mượt trên thiết bị cấu hình yếu.

Phạm vi thay đổi ảnh hưởng hiệu năng
- Debounce tìm kiếm: chuyển onkeyup → oninput và áp dụng debounce 300ms trong JS (giảm reflow khi nhập).
- Giảm chuyển động khi người dùng bật prefers-reduced-motion; tắt/giảm animation nặng (nền, card shimmer/float).
- Chuẩn hóa toast, autosave indicator để tránh inline style layout-thrashing; tạo/lấp DOM có kiểm soát.
- Thêm skeleton/loading nhẹ với overlay dựa trên CSS class thay vì inline style.
- Tối ưu trạng thái error/empty state (ẩn/hiện bằng class, tránh detach/attach cây DOM lớn).

File liên quan
- UI: web/templates/index.html
- CSS: web/static/enhancements.css
- JS: web/static/enhancements.js
- Tài liệu: README.md, STYLEGUIDE.md, TESTING.md

Cách đo thủ công (Chrome DevTools)
1) Mở trang trên Replit (nút Run như cũ), truy cập URL trang chủ.
2) Mở DevTools → Tab Performance:
   - Chọn “Screenshots” và “Web Vitals”.
   - CPU Throttling: 4×, Network: Slow 3G (đo kịch bản xấu).
   - Reload trang (Ctrl+R) để ghi trace.
3) Ghi lại các chỉ số:
   - FCP (First Contentful Paint)
   - LCP (Largest Contentful Paint)
   - TTI (Time to Interactive)
   - CLS (Cumulative Layout Shift)
4) Lặp lại 3 lần, lấy trung vị (median) để giảm nhiễu.

Cách đo bổ sung (Lighthouse)
- DevTools → Lighthouse → Performance (Desktop + Mobile), Simulated throttling bật mặc định.
- So sánh điểm Performance trước/sau (ghi chú: chỉ số thay đổi do môi trường Replit).

Kỳ vọng cải thiện (định tính)
- FCP: cải thiện nhẹ do giảm layout thrashing của các phần tử toast/indicator.
- LCP: duy trì ổn định; các thành phần lớn (header, container) ít bị reflow do chuyển sang transition có kiểm soát.
- TTI: cải thiện nhờ debounce tìm kiếm và giảm handler tần suất cao.
- CLS: giảm do focus-visible, skeleton/empty/error state sử dụng không gây shift bố cục.

Gợi ý mục tiêu (tham khảo trên thiết bị trung bình, mạng 3G mô phỏng)
- FCP: ~1.5s–2.5s (Mobile)
- LCP: ~2.0s–3.0s (Mobile)
- TTI: ~2.5s–3.5s (Mobile)
Lưu ý: Replit thêm độ trễ mạng/CPU; kết quả có thể lớn hơn máy cục bộ.

Kịch bản kiểm chứng nhanh
- Reload lạnh (hard reload) trên Mobile throttling.
- Nhập nhanh 15–30 ký tự vào ô tìm kiếm: không lag đáng kể; DOM cập nhật có kiểm soát.
- Bật prefers-reduced-motion ở hệ điều hành: nền và card animation hầu như tắt.

Các thay đổi cụ thể giúp hiệu năng
- Debounce tìm kiếm: giảm số lần gọi filter/sort và cập nhật DOM.
- Skeleton bằng pseudo overlay trên card/stats: không xây dựng DOM mới cho placeholder.
- Reduced motion: loại animation nặng (gradient float, shimmer) khi người dùng chọn hạn chế chuyển động.
- Toast container và item có class show/ẩn với transition thay vì style inline dòng dài.
- Error/empty state: dựng một lần, toggle display/class (ẩn/hiện) thay vì render lại toàn bộ lưới.

Giải thích trade-offs
- Vẫn giữ nền gradient/hiệu ứng cho trải nghiệm thị giác; đã giảm cường độ khi prefers-reduced-motion bật.
- Chưa áp dụng code splitting/lazy load JS vì không thay đổi build tool và kiến trúc bundle hiện tại (yêu cầu đảm bảo khả năng chạy nguyên trạng trên Replit).
- Giữ CDN Bootstrap/FontAwesome để đảm bảo tính tương thích rộng.

Checklist tối ưu tiếp theo (không bắt buộc, an toàn với Replit)
- Tách phần CSS inline trong index.html sang enhancements.css theo module để giảm inline style parse-time.
- Prefetch nhẹ icon/font (rel=preconnect đã có); cân nhắc preload hợp lý (chỉ khi xác định lợi ích rõ ràng).
- Trì hoãn script không cần thiết (defer đã dùng); tránh các handler inline lặp.
- Hạn chế box-shadow nặng trong viewport khi scroll dài (đã giảm trên mobile/reduced motion).
- Theo dõi console cảnh báo và memory leak; tháo bỏ listener khi modal đóng (nếu thêm trong tương lai).

Cách ghi nhận và báo cáo
- Sử dụng Performance panel + Lighthouse: chụp ảnh (png) và lưu kết quả vào thư mục logs/ hoặc đính kèm vào CHANGELOG.md.
- Ghi chú cấu hình đo (throttling, độ phân giải, state dark/light) để đảm bảo tái lập.

Feature flags (khuyến nghị nhẹ)
- Dùng localStorage để bật tắt một số hiệu ứng (optional):
  - uiFlags = { animations: true, toasts: true }
  - Khi cần test: localStorage.setItem('uiFlags', JSON.stringify({animations:false}))
  - JS đọc cờ để vô hiệu một số hiệu ứng (hiện chưa bật mặc định để tránh rủi ro đổi hành vi).

Lưu ý tương thích
- Không thay đổi cấu hình .replit, replit.nix, Procfile, lệnh run hoặc URL/API.
- Không thêm phụ thuộc ngoài; tất cả thay đổi chạy thuần trình duyệt/Flask.

Phụ lục: thuật ngữ
- FCP: thời điểm phần tử nội dung đầu tiên vẽ ra.
- LCP: thời điểm phần tử nội dung lớn nhất vẽ ra (thường là headline/container lớn).
- TTI: thời điểm trang sẵn sàng phản hồi tương tác đáng tin cậy.
- CLS: mức độ dịch chuyển bố cục khi tải.

Kết luận
- Nâng cấp giúp trải nghiệm tương tác mượt hơn, đặc biệt trong tìm kiếm và trạng thái tải.
- Chỉ số Web Vitals kỳ vọng ổn định hơn trong điều kiện mạng yếu do giảm thao tác DOM thừa và tôn trọng reduced motion.