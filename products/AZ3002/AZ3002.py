import os
import random
from datetime import datetime
import xlwings as xw
import data

random.seed(datetime.now().timestamp())

# Cấu hình randbetween E → N (10 cột)
rand_config = [
    (8515, 9105, True),    # E
    (8515, 9105, True),    # F
    (28513, 31005, True),  # G
    (12503, 13845, True),  # H
    (3200, 3400, False),   # I
    (900, 1000, False),    # J
    (1815, 1950, False),   # K
    (515, 605, False),     # L
    (6325, 7105, True),    # M
    (5218, 6195, True)     # N
]

cols = list("EFGHIJKLMN")

def generate_unique_randoms(a, b, count):
    result = set()
    while len(result) < count:
        result.add(random.randint(a, b))
    return list(result)

def apply_center(ws, cell_range):
    rng = ws.range(cell_range)
    rng.api.HorizontalAlignment = -4108
    rng.api.VerticalAlignment = -4108

def main():
    file_name = f"{data.product_name} - PO# {data.po_number} - {data.date_code}"
    today_folder = datetime.today().strftime("%Y-%m-%d")
    output_dir = os.path.join(data.output_root, today_folder, file_name)
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, f"{file_name}.xlsx")

    app = xw.App(visible=False)
    wb = app.books.open(data.template_file)
    ws = wb.sheets[0]

    # Ghi serial vào A11:A15
    for i, sn in enumerate(data.serial_numbers):
        cell = f"A{11+i}"
        ws.range(cell).value = sn
        apply_center(ws, cell)

    # Ghi dữ liệu random vào E11:N15
    for col_idx, (a, b, divide) in enumerate(rand_config):
        values = generate_unique_randoms(a, b, 5)
        for row_idx in range(5):
            val = round(values[row_idx] / 100, 2) if divide else values[row_idx]
            cell = f"{cols[col_idx]}{11+row_idx}"
            ws.range(cell).value = val
            apply_center(ws, cell)

    # Xử lý PO tại H4:M5
    ws.range("H4").value = data.po_number
    apply_center(ws, "H4:M5")
    ws.range("H4:M5").merge()

    # Ngày tháng tại T4:W5
    formatted_date = datetime.strptime(data.date_code, "%Y%m%d").strftime("%Y.%m.%d")
    ws.range("T4").value = formatted_date
    apply_center(ws, "T4:W5")
    ws.range("T4:W5").merge()
    
    # Ghi tên sản phẩm vào C4:D5
    ws.range("C4").value = data.product_name
    apply_center(ws, "C4:D5")

    # Căn giữa thêm cho bảng
    apply_center(ws, "A11:A15")
    apply_center(ws, "E11:N15")

    wb.save(save_path)
    wb.close()
    app.quit()

    print(f"✅ File đã lưu tại: {save_path}")

if __name__ == "__main__":
    main()
