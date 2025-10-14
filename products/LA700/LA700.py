import xlwings as xw
from datetime import datetime
import os
import random
import data

random.seed(datetime.now().timestamp())

# Cấu hình RANDBETWEEN cho E → N (10 cột)
rand_config = [
    (7700, 8600, True),   # E
    (6700, 7400, True),   # F
    (18500, 19500, True), # G
    (8000, 9800, True),   # H
    (3200, 3500, False),  # I
    (850, 1000, False),   # J
    (1750, 1950, False),  # K
    (500, 600, False),    # L
    (5200, 5600, True),   # M
    (4500, 5300, True)    # N
]

cols = list("EFGHIJKLMN")

def generate_unique_randoms(a, b, count):
    """Generate unique random values within the specified range."""
    result = set()
    while len(result) < count:
        result.add(random.randint(a, b))
    return list(result)

def apply_center(ws, cell_range):
    """Center align text in a given cell range."""
    rng = ws.range(cell_range)
    rng.api.HorizontalAlignment = -4108  # xlCenter
    rng.api.VerticalAlignment = -4108    # xlCenter

def create_file_path():
    """Create the file path based on product name, PO, and date code."""
    file_name = f"{data.product_name} - PO# {data.po_number} - {data.date_code}"
    today_folder = datetime.now().strftime("%Y-%m-%d")
    output_root = os.path.join(data.output_root, today_folder)
    file_folder = os.path.join(output_root, file_name)
    os.makedirs(file_folder, exist_ok=True)
    return os.path.join(file_folder, f"{file_name}.xlsx")

def write_data_to_sheet(ws):
    """Write serial numbers and random values to the sheet."""
    # Ghi serial vào A11:A15
    for i, sn in enumerate(data.serial_numbers):
        cell = f"A{11+i}"
        ws.range(cell).value = sn
        apply_center(ws, cell)

    # Ghi random vào E11:N15 (10 cột, không trùng theo cột)
    for col_idx, (a, b, divide) in enumerate(rand_config):
        values = generate_unique_randoms(a, b, 5)
        for row_idx in range(5):
            val = round(values[row_idx] / 100, 2) if divide else values[row_idx]
            cell = f"{cols[col_idx]}{11+row_idx}"
            ws.range(cell).value = val
            apply_center(ws, cell)

def main():
    """Main function to generate the Excel file."""
    # Kiểm tra sự tồn tại của template
    if not os.path.exists(data.template_file):
        print(f"❌ Template không tồn tại: {data.template_file}")
        return

    save_path = create_file_path()

    # Mở Excel với 'with' để tự động đóng app khi xong
    with xw.App(visible=False) as app:
        wb = app.books.open(data.template_file)
        ws = wb.sheets[0]

        write_data_to_sheet(ws)
        
        # Ghi tên sản phẩm vào C4:D5
        ws.range("C4").value = data.product_name
        apply_center(ws, "C4:D5")

        # Ghi PO vào H4 (merged H4:M5)
        ws.range("H4").value = data.po_number
        apply_center(ws, "H4:M5")

        # Ghi ngày tháng vào T4 (merged T4:W5)
        formatted_date = datetime.strptime(data.date_code, "%Y%m%d").strftime("%Y.%m.%d")
        ws.range("T4").value = formatted_date
        apply_center(ws, "T4:W5")

        # Căn giữa bảng dữ liệu chính
        apply_center(ws, "E11:N15")

        # Lưu và đóng workbook
        wb.save(save_path)

    print(f"✅ File đã lưu tại: {save_path}")

if __name__ == "__main__":
    main()
