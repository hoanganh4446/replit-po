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

- Email: your.email@example.com
- GitHub: [@yourusername](https://github.com/yourusername)

## 🙏 Acknowledgments

- Flask team cho framework tuyệt vời
- Bootstrap team cho UI components
- Replit team cho platform deployment# replit-po
