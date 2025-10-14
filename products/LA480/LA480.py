import xlwings as xw
from datetime import datetime
import os
import random
import data

random.seed(datetime.now().timestamp())

# Cấu hình randbetween cho E→L
rand_config = [
    (7280, 7926, True),   # E
    (6903, 7761, True),   # F
    (18000, 19700, True), # G
    (8700, 9783, True),  # H
    (747, 910, False),   # I
    (3320, 3690, False),  # J
    (5136, 5960, True),   # K
    (4510, 4940, True),   # L
]

cols = list("EFGHIJKL")

def generate_unique_randoms(a, b, count):
    result = set()
    while len(result) < count:
        result.add(random.randint(a, b))
    return list(result)

def apply_center_xlwings(sheet, cell_range):
    rng = sheet.range(cell_range)
    rng.api.HorizontalAlignment = -4108  # xlCenter
    rng.api.VerticalAlignment = -4108    # xlCenter

def main():
    file_name = f"{data.product_name} - PO#{data.po_number} - {data.date_code}"
    today_folder = datetime.today().strftime("%Y-%m-%d")
    output_root = os.path.join(data.output_root, today_folder)
    file_folder = os.path.join(output_root, file_name)
    os.makedirs(file_folder, exist_ok=True)
    save_path = os.path.join(file_folder, f"{file_name}.xlsx")

    app = xw.App(visible=False)
    wb = app.books.open(data.template_file)
    ws = wb.sheets[0]

    # Serial A11:A15
    for i, sn in enumerate(data.serial_numbers):
        ws.range(f"A{11+i}").value = sn

    # Random E11:L15 – mỗi cột không trùng trong 5 giá trị
    for col_idx, (a, b, divide) in enumerate(rand_config):
        values = generate_unique_randoms(a, b, 5)
        for row_idx in range(5):
            val = round(values[row_idx] / 100, 2) if divide else values[row_idx]
            ws.range(f"{cols[col_idx]}{11+row_idx}").value = val

    # Ghi tên sản phẩm vào C4
    ws.range("C4").value = data.product_name
    apply_center_xlwings(ws, "C4:D5")

    # Ghi số PO vào H4
    ws.range("H4").value = data.po_number
    apply_center_xlwings(ws, "H4:K5")

    # Ghi ngày tháng vào R4
    formatted_date = datetime.strptime(data.date_code, "%Y%m%d").strftime("%Y.%m.%d")
    ws.range("R4").value = formatted_date
    apply_center_xlwings(ws, "R4:U5")

    # Căn giữa các vùng dữ liệu
    apply_center_xlwings(ws, "A11:A15")
    apply_center_xlwings(ws, "E11:L15")

    wb.save(save_path)
    wb.close()
    app.quit()

    print(f"✅ Đã tạo file tại: {save_path}")

if __name__ == "__main__":
    main()
