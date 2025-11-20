# PO System - Production Order Management System

Hệ thống quản lý đơn hàng sản xuất (PO System) được phát triển bằng Flask, hỗ trợ tạo và quản lý các file Excel PO tự động.

## 🚀 Tính năng chính

- **Dashboard Analytics**: Theo dõi và phân tích dữ liệu PO
- **Bulk Operations**: Xử lý hàng loạt nhiều PO cùng lúc
- **Advanced Search**: Tìm kiếm nâng cao với nhiều tiêu chí
- **Export/Import Data**: Xuất nhập dữ liệu linh hoạt
- **User Management**: Quản lý người dùng và phân quyền
- **Real-time Monitoring**: Giám sát hệ thống real-time

## 🛠️ Công nghệ sử dụng

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **Database**: SQLite
- **Excel Processing**: openpyxl
- **Deployment**: Replit, GitHub

## 📦 Cài đặt và chạy

### Trên Replit

1. Fork repository này trên GitHub
2. Import vào Replit từ GitHub
3. Replit sẽ tự động cài đặt dependencies từ `requirements.txt`
4. Chạy ứng dụng bằng cách click "Run" hoặc chạy `python main.py`

### Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/po-system-deployment.git
cd po-system-deployment

# Tạo virtual environment
python -m venv venv
source venv/bin/activate  # Trên Windows: venv\Scripts\activate

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy ứng dụng
python main.py
```

## 📁 Cấu trúc dự án

```
po-system-deployment/
├── main.py                 # Entry point cho Replit
├── requirements.txt        # Python dependencies
├── .replit                # Replit configuration
├── replit.nix            # Replit Nix configuration
├── .gitignore            # Git ignore rules
├── src/
│   ├── apps/
│   │   └── app.py        # Main Flask application
│   ├── core/             # Core modules
│   ├── managers/         # Business logic managers
│   └── utils/            # Utility functions
├── web/
│   ├── templates/        # HTML templates
│   └── static/           # CSS, JS, images
└── products/             # Product configurations và templates
```

## 🔧 Cấu hình

### Environment Variables

- `PORT`: Port cho ứng dụng (mặc định: 5000)
- `FLASK_ENV`: Environment mode (development/production)
- `FLASK_DEBUG`: Debug mode (True/False)

### Product Configuration

Mỗi sản phẩm trong folder `products/` chứa:

- `data.py`: Cấu hình sản phẩm
- `*.py`: Logic xử lý sản phẩm
- `*.xlsx`: Template Excel

## 📊 API Endpoints

- `GET /`: Trang chủ
- `GET /dashboard`: Dashboard analytics
- `GET /api/products`: Danh sách sản phẩm
- `POST /api/generate`: Tạo file PO
- `GET /api/history`: Lịch sử tạo file
- `POST /api/bulk`: Xử lý hàng loạt

## 🚀 Deployment

### Replit

- Tự động deploy khi push code lên GitHub
- Sử dụng `main.py` làm entry point
- Port được set tự động từ environment

### Render.com

- Xem hướng dẫn chi tiết tại [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)
- Sử dụng `render.yaml` configuration
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn --bind 0.0.0.0:$PORT src.apps.app:app`

## 🤝 Đóng góp

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📞 Liên hệ

- Email: <your.email@example.com>
- GitHub: [@yourusername](https://github.com/yourusername)

## 🙏 Acknowledgments

- Flask team cho framework tuyệt vời
- Bootstrap team cho UI components
- Replit team cho platform deployment# replit-po

## 🧩 Nâng cấp UI/UX & Hiệu năng (2025-11-09)

Các thay đổi đã triển khai nhằm hiện đại hóa giao diện, nâng cao trải nghiệm người dùng, và tối ưu hiệu năng mà không thay đổi nền tảng hay luồng chạy trên Replit:

- Giao diện:
  - Dark mode và chuyển theme trực tiếp trên thanh tác vụ; tự động theo prefers-color-scheme.
  - A11y: thêm skip link, role="main", focus-visible rõ ràng, aria-live cho thông báo.
  - Micro-interactions tinh tế, trạng thái rỗng (empty state) khi không có kết quả, skeleton/loading states nhẹ.
- Hiệu năng:
  - Debounce tìm kiếm theo sự kiện input, giảm reflow/repaint khi nhập nhanh.
  - Prefers-reduced-motion để giảm animation nặng trên thiết bị nhạy cảm hoặc cấu hình yếu.
  - Đồng bộ toast sử dụng container và class để tránh inline style và hạn chế layout thrashing.
- Chất lượng:
  - Hợp nhất autosave indicator (#saveIndicator), loại bỏ phần trùng lặp và inline style dư thừa.
  - Chuẩn hóa CSS/JS để dễ bảo trì, không thay đổi API, đường dẫn, hoặc hành vi cốt lõi.

Tham chiếu các tập tin liên quan:

- UI chính: [web/templates/index.html](web/templates/index.html)
- CSS nâng cấp: [web/static/enhancements.css](web/static/enhancements.css)
- JS nâng cấp: [web/static/enhancements.js](web/static/enhancements.js)

## ⚙️ Hướng dẫn chạy trên Replit (không thay đổi lệnh run)

- Vẫn chạy qua entry point [main.py](main.py) hoặc nút "Run" của Replit.
- Replit tự động gán PORT qua biến môi trường; không cần chỉnh sửa cấu hình.
- Không thay đổi `.replit`, `replit.nix`, lệnh run hay cấu trúc thư mục.

## ♿ Accessibility (WCAG 2.1 AA tiệm cận)

- Bỏ qua điều hướng: có skip link “Bỏ qua điều hướng…” nhảy tới nội dung chính.
- Focus rõ ràng: sử dụng :focus-visible với outline tương phản.
- Thông báo: toast có aria-live="polite", autosave indicator không gây nhiễu.
- Tương phản màu: màu sắc được chọn đáp ứng mức tương phản ở chế độ sáng/tối.
- Bàn phím: hỗ trợ phím tắt (Ctrl/Cmd + K để focus tìm kiếm, Ctrl/Cmd + D chuyển dark mode).

## 🎨 Styleguide

- Xem tài liệu chi tiết hệ thống thiết kế: [STYLEGUIDE.md](STYLEGUIDE.md)
  - Typography scale, màu sắc chính/phụ, spacing, iconography, trạng thái tương tác.
  - Quy ước class CSS và guideline viết component (HTML/CSS/JS) nhất quán.

## 🧪 Kiểm thử

- Hướng dẫn kiểm thử, phạm vi, và cách tái chạy: [TESTING.md](TESTING.md)
  - Test đơn vị/tích hợp cơ bản cho các luồng quan trọng.
  - Checklist truy cập nhanh để xác nhận UI/UX và A11y.

## 📈 Báo cáo hiệu năng

- Trước/Sau nâng cấp, các chỉ số và cách tự đo (LCP/FCP/TTI) được mô tả trong [PERFORMANCE.md](PERFORMANCE.md).
- Hướng dẫn sử dụng DevTools và cấu hình đo tại chỗ trên Replit.

## 🚩 Feature Flags / Config

- Dark mode: lưu trạng thái qua localStorage; phím tắt Ctrl/Cmd + D và nút trên taskbar.
- Có thể mở rộng flags cho các tính năng mới; mặc định không bật các tính năng có rủi ro.

## 🔄 Migration

- Không có thay đổi schema dữ liệu hay API công khai trong đợt nâng cấp này.
- Không yêu cầu script migrate hoặc thay đổi biến môi trường.

## 📝 Changelog

- Tóm tắt thay đổi chi tiết theo từng phiên bản: [CHANGELOG.md](CHANGELOG.md)
