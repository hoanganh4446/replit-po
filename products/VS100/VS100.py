import xlwings as xw
from datetime import datetime
import os
import random
import data

random.seed(datetime.now().timestamp())

cols = ["E", "F", "G"]

def generate_unique_row_e_to_g():
    while True:
        row = [
            round(random.randint(8000, 8450) / 100, 2),
            round(random.randint(14400, 15300) / 100, 2),
            round(random.randint(4210, 4590) / 100, 2),
        ]
        if len(set(row)) == len(row):  # Đảm bảo giá trị không trùng
            return row

def main():
    file_name = f"{data.product_name} - PO# {data.po_number} - {data.date_code}"
    today_folder = datetime.today().strftime("%Y-%m-%d")
    output_root = os.path.join(data.OUTPUT_ROOT, today_folder)
    file_folder = os.path.join(output_root, file_name)
    os.makedirs(file_folder, exist_ok=True)
    save_path = os.path.join(file_folder, f"{file_name}.xlsx")

    if not os.path.exists(data.TEMPLATE_FILE):  # Kiểm tra nếu template không tồn tại
        print(f"❌ Template không tồn tại: {data.TEMPLATE_FILE}")
        return

    with xw.App(visible=False) as app:  # Sử dụng 'with' để đảm bảo app đóng khi xong
        wb = app.books.open(data.TEMPLATE_FILE)
        ws = wb.sheets[0]

        # Serial A11:A15
        for i, sn in enumerate(data.serial_numbers):
            ws.range(f"A{11+i}").value = sn

        # Random E11:G15 – mỗi hàng một bộ giá trị không trùng
        for row_idx in range(5):
            values = generate_unique_row_e_to_g()
            for col_idx, val in enumerate(values):
                ws.range(f"{cols[col_idx]}{11+row_idx}").value = val

        # Tên sản phẩm C4 (merge C4:D5)
        ws.range("C4").value = data.product_name

        # PO tại F4 (merge F4:G5)
        ws.range("F4").value = data.po_number

        # Ngày tại M4 (merge M4:P5)
        formatted_date = datetime.strptime(data.date_code, "%Y%m%d").strftime("%Y.%m.%d")
        ws.range("M4").value = formatted_date

        # Căn giữa
        ws.range("A11:G15").api.HorizontalAlignment = -4108
        ws.range("A11:G15").api.VerticalAlignment = -4108
        ws.range("C4:D5").api.HorizontalAlignment = -4108
        ws.range("F4:G5").api.HorizontalAlignment = -4108
        ws.range("M4:P5").api.HorizontalAlignment = -4108

        # Lưu và đóng
        wb.save(save_path)
        wb.close()

    print(f"✅ Đã tạo file tại: {save_path}")

if __name__ == "__main__":
    main()
