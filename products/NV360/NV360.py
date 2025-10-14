import xlwings as xw
from datetime import datetime
import os
import random
import data

random.seed(datetime.now().timestamp())

# Cấu hình RANDBETWEEN cho từng cột E → K
rand_config = {
    "E": (8225, 9546, True),
    "F": (6225, 7546, True),
    "G": (18525, 21546, True),
    "H": (9225, 10546, True),
    "I": (4225, 4546, False),
    "J": (5225, 6546, True),
    "K": (4225, 5346, True),
}

def generate_unique_row(used, a, b):
    """Generate a unique random value within the specified range."""
    while True:
        val = random.randint(a, b)
        if val not in used:
            used.add(val)
            return val

def apply_center_xlwings(sheet, cell_range):
    """Apply center alignment to a specified cell range."""
    rng = sheet.range(cell_range)
    rng.api.HorizontalAlignment = -4108  # xlCenter
    rng.api.VerticalAlignment = -4108    # xlCenter

def main():
    # Đường dẫn và tên file
    file_name = f"{data.product_name} - PO#{data.po_number} - {data.date_code}"
    today_folder = datetime.today().strftime("%Y-%m-%d")
    output_root = os.path.join(data.output_root, today_folder)
    file_folder = os.path.join(output_root, file_name)
    os.makedirs(file_folder, exist_ok=True)
    save_path = os.path.join(file_folder, f"{file_name}.xlsx")

    # Kiểm tra sự tồn tại của template
    if not os.path.exists(data.template_file):
        print(f"❌ Template không tồn tại: {data.template_file}")
        return

    # Mở Excel với 'with' để tự động đóng app khi xong
    with xw.App(visible=False) as app:
        wb = app.books.open(data.template_file)
        ws = wb.sheets[0]

        # Ghi số tem vào A11:A15
        for i, sn in enumerate(data.serial_numbers):
            ws.range(f"A{11+i}").value = sn

        # Ghi giá trị random E11:K15
        for row_idx in range(5):
            used = set()
            for col_letter, (a, b, divide) in rand_config.items():
                val = generate_unique_row(used, a, b)
                result = round(val / 100, 2) if divide else val
                ws.range(f"{col_letter}{11+row_idx}").value = result

        # Ghi tên sản phẩm tại C4 (merge C4:D5)
        ws.range("C4").value = data.product_name
        apply_center_xlwings(ws, "C4:D5")

        # Ghi số PO tại H4 (merge H4:J5)
        ws.range("H4").value = data.po_number
        apply_center_xlwings(ws, "H4:J5")

        # Ghi ngày tháng tại Q4 (merge Q4:T5) - định dạng yyyy.mm.dd
        formatted_date = datetime.strptime(data.date_code, "%Y%m%d").strftime("%Y.%m.%d")
        ws.range("Q4").value = formatted_date
        apply_center_xlwings(ws, "Q4:T5")

        # Căn giữa tất cả vùng dữ liệu
        apply_center_xlwings(ws, "A11:K15")

        # Lưu và đóng workbook
        wb.save(save_path)

    print(f"✅ Đã tạo file tại: {save_path}")

if __name__ == "__main__":
    main()
