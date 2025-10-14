import xlwings as xw
from datetime import datetime
import os
import random
import data  # file data.py chứa thông tin đầu vào

def generate_random_values():
    return {
        'B': [random.randint(830, 860) for _ in range(5)],
        'C': [random.randint(1130, 1170) for _ in range(5)],
        'D': [random.randint(1675, 1720) for _ in range(5)],
        'E': [random.randint(2025, 2060) for _ in range(5)],
        'F': [random.randint(2370, 2410) for _ in range(5)],
        'G': [round(random.randint(30, 49) / 100, 2) for _ in range(5)],
        'H': [round(random.randint(430, 550) / 100, 2) for _ in range(5)],
        'I': [round(random.randint(780, 900) / 100, 2) for _ in range(5)],
        'J': [round(random.randint(170, 195) / 10, 1) for _ in range(5)],
        'K': [round(random.randint(295, 330) / 10, 1) for _ in range(5)],
        'L': [round(random.randint(500, 543) / 10, 1) for _ in range(5)],
    }

def main():
    # Tạo tên file và thư mục theo ngày
    file_name = f"{data.product_name} - PO# {data.po_number} - {data.date_code}"
    today_folder = datetime.today().strftime("%Y-%m-%d")
    output_root = os.path.join(data.OUTPUT_ROOT, today_folder)
    file_folder = os.path.join(output_root, file_name)
    os.makedirs(file_folder, exist_ok=True)
    save_path = os.path.join(file_folder, f"{file_name}.xlsx")

    # Mở Excel bằng xlwings (Excel thật)
    app = xw.App(visible=False)
    wb = app.books.open(data.TEMPLATE_FILE)
    ws = wb.sheets[0]

    # Ghi serial vào A11:A15
    for i, sn in enumerate(data.serial_numbers):
        ws.range(f"A{11+i}").value = sn

    # Ghi giá trị random vào B11:L15
    rand_vals = generate_random_values()
    for col, values in rand_vals.items():
        for i, val in enumerate(values):
            ws.range(f"{col}{11+i}").value = val
   
    # Ghi tên sản phẩm vào C4
    ws.range("C4").value = data.product_name

    # Ghi PO vào I4
    ws.range("I4").value = f"PO# {data.po_number}"

    # Ghi ngày định dạng yyyy-mm-dd vào M4
    formatted_date = datetime.strptime(data.date_code, "%Y%m%d").strftime("%Y.%m.%d")
    ws.range("M4").value = formatted_date

    # Căn giữa nội dung đã ghi
    ws.range("A11:L15").api.HorizontalAlignment = -4108  # center
    ws.range("A11:L15").api.VerticalAlignment = -4108    # middle
    ws.range("I4:L5").api.HorizontalAlignment = -4108
    ws.range("M4:N5").api.HorizontalAlignment = -4108

    # Lưu và đóng
    wb.save(save_path)
    wb.close()
    app.quit()

    print(f"✅ Đã tạo file tại: {save_path}")

if __name__ == "__main__":
    main()
