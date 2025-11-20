# Hướng Dẫn Triển Khai PO System Lên Render.com

Tài liệu này hướng dẫn chi tiết cách triển khai ứng dụng PO System lên Render.com để chạy 24/7.

## 1. Chuẩn Bị

Đảm bảo bạn đã có:

1. Tài khoản GitHub (hoặc GitLab/Bitbucket).
2. Tài khoản Render.com.
3. Code đã được push lên GitHub repository.

## 2. Cấu Hình Project (Đã thực hiện)

Các file cấu hình đã được chuẩn bị sẵn:

- **`render.yaml`**: Blueprint file định nghĩa cấu trúc hạ tầng trên Render.
- **`Procfile`**: Định nghĩa lệnh khởi chạy ứng dụng (sử dụng Gunicorn).
- **`requirements.txt`**: Danh sách các thư viện cần thiết.
- **`wsgi.py`**: Entry point cho Gunicorn.
- **`src/apps/app.py`**: Đã được cập nhật để hỗ trợ lưu trữ dữ liệu bền vững (Persistent Disk).

## 3. Các Bước Triển Khai

### Cách 1: Sử dụng Blueprint (Khuyên dùng)

Đây là cách nhanh nhất và tự động nhất vì nó sử dụng file `render.yaml`.

1. Đăng nhập vào [Render Dashboard](https://dashboard.render.com/).
2. Chọn **New +** -> **Blueprint**.
3. Kết nối với GitHub repository của bạn.
4. Đặt tên cho Service Group (ví dụ: `po-system-prod`).
5. Render sẽ tự động phát hiện file `render.yaml` và hiển thị các resource sẽ được tạo:
   - **Web Service**: `po-system-web` (Python app).
   - **Disk**: `po-system-data` (Lưu trữ database và logs).
6. Nhấn **Apply** hoặc **Create Blueprint**.
7. Chờ Render build và deploy (khoảng 3-5 phút).

### Cách 2: Cấu Hình Thủ Công (Web Service)

Nếu bạn không muốn dùng Blueprint:

1. Chọn **New +** -> **Web Service**.
2. Kết nối repository.
3. Điền thông tin:
   - **Name**: `po-system`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT wsgi:app`
4. Vào tab **Environment**:
   - Thêm `PYTHON_VERSION`: `3.11.0`
   - Thêm `DATA_DIR`: `/opt/render/project/src/data` (Quan trọng để lưu dữ liệu)
5. Vào tab **Disks**:
   - Tạo disk mới.
   - **Mount Path**: `/opt/render/project/src/data`
   - **Size**: 1GB.
6. Nhấn **Create Web Service**.

## 4. Lưu Ý Quan Trọng

### Dữ Liệu Bền Vững (Persistent Data)

- Render Web Services là **ephemeral** (tạm thời). Mọi file bạn lưu vào hệ thống file thông thường sẽ bị mất khi redeploy hoặc restart.
- Chúng tôi đã cấu hình **Render Disk** gắn vào đường dẫn `/opt/render/project/src/data`.
- Database (`po_system.db`), logs, và file output sẽ được lưu vào disk này để đảm bảo dữ liệu không bị mất.

### Timezone

- Timezone đã được set là `Asia/Ho_Chi_Minh` để đảm bảo giờ hiển thị đúng với Việt Nam.

### Logs

- Bạn có thể xem logs trực tiếp trên Render Dashboard tab **Logs**.
- Logs cũng được lưu vào file trong thư mục data nếu cần debug sâu hơn.

## 5. Troubleshooting

- **Lỗi Build**: Kiểm tra tab Logs phần Build. Thường do lỗi version trong `requirements.txt`.
- **Lỗi Start**: Kiểm tra tab Logs phần Deploy. Nếu thấy lỗi "Module not found", kiểm tra lại cấu trúc thư mục.
- **Lỗi Database**: Nếu dữ liệu bị mất sau khi deploy lại, kiểm tra xem Disk đã được mount đúng vào `/opt/render/project/src/data` chưa và biến môi trường `DATA_DIR` đã được set chưa.
