# Hướng dẫn Deploy PO System lên Replit

## 🚀 Các bước deploy

### 1. Chuẩn bị GitHub Repository

1. Tạo repository mới trên GitHub
2. Upload toàn bộ code lên GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit - PO System for Replit"
   git branch -M main
   git remote add origin https://github.com/yourusername/po-system-replit.git
   git push -u origin main
   ```

### 2. Import vào Replit

1. Truy cập [Replit](https://replit.com/)
2. Click "Create Repl"
3. Chọn "Import from GitHub"
4. Nhập URL repository GitHub
5. Click "Import"

### 3. Cấu hình Replit

Replit sẽ tự động:
- Đọc file `.replit` để cấu hình environment
- Cài đặt dependencies từ `requirements.txt`
- Sử dụng `main.py` làm entry point

### 4. Chạy ứng dụng

1. Click nút "Run" trên Replit
2. Hoặc chạy command: `python main.py`
3. Ứng dụng sẽ chạy trên port được Replit assign

## 📁 Cấu trúc file quan trọng

- `main.py`: Entry point cho Replit
- `.replit`: Cấu hình Replit environment
- `replit.nix`: Nix packages configuration
- `requirements.txt`: Python dependencies (đã loại bỏ xlwings)
- `src/apps/app.py`: Main Flask application
- `products/`: Folder chứa templates Excel và config sản phẩm

## ⚠️ Lưu ý quan trọng

### Folder Products
- **PHẢI** upload toàn bộ folder `products/` lên GitHub
- Folder này chứa templates Excel và config cho từng sản phẩm
- Nếu thiếu sẽ bị lỗi khi tạo file Excel

### Dependencies đã thay đổi
- Loại bỏ `xlwings` (không tương thích với Replit)
- Sử dụng `openpyxl` thay thế
- Đã thêm các method `process_*_openpyxl()` trong `ExcelProcessor`

### Đường dẫn đã sửa
- Tất cả `localhost` đã chuyển thành `0.0.0.0`
- Đường dẫn templates và static đã điều chỉnh cho Replit
- BASE_DIR được detect tự động

## 🔧 Troubleshooting

### Lỗi import xlwings
- Đã loại bỏ hoàn toàn xlwings
- Sử dụng openpyxl thay thế

### Lỗi đường dẫn file
- Kiểm tra folder `products/` đã upload đầy đủ
- Đảm bảo templates Excel có trong từng subfolder

### Lỗi port
- Replit tự động assign port qua environment variable `PORT`
- Code đã được sửa để sử dụng `os.environ.get("PORT", 5000)`

## 📊 Monitoring

Sau khi deploy thành công:
- Truy cập URL được Replit cung cấp
- Kiểm tra các endpoint:
  - `/` - Trang chủ
  - `/dashboard` - Dashboard analytics
  - `/api/products` - API sản phẩm

## 🔄 Update code

Để update code:
1. Sửa code local
2. Push lên GitHub
3. Replit sẽ tự động sync và restart
