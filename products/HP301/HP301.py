import xlwings as xw
from datetime import datetime
import os
import random
import data

random.seed(datetime.now().timestamp())

# Cấu hình randbetween cho B → L (11 cột)
rand_config = [
    (825, 855, False),       # B
    (1125, 1150, False),     # C
    (1670, 1720, False),     # D
    (2030, 2060, False),     # E
    (2375, 2415, False),     # F
    (30, 48, "div100"),      # G
    (420, 589, "div100"),    # H
    (790, 910, "div100"),    # I
    (178, 205, "div10"),     # J
    (299, 328, "div10"),     # K
    (502, 543, "div10"),     # L
]

cols = list("BCDEFGHIJKL")

def apply_center(ws, cell_range):
    rng = ws.range(cell_range)
    rng.api.HorizontalAlignment = -4108  # center
    rng.api.VerticalAlignment = -4108    # middle

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

    # Ghi serial A11:A15
    for i, sn in enumerate(data.serial_numbers):
        cell = ws.range(f"A{11+i}")
        cell.value = sn
        apply_center(ws, cell.address)

    # Ghi random vào B11:L15 theo cấu hình, không trùng mỗi dòng
    for row in range(5):
        used_values = set()
        for col_idx, (a, b, mode) in enumerate(rand_config):
            while True:
                val = random.randint(a, b)
                if val not in used_values:
                    used_values.add(val)
                    break
            if mode == "div100":
                val = round(val / 100, 2)
            elif mode == "div10":
                val = round(val / 10, 1)
            cell_addr = f"{cols[col_idx]}{11+row}"
            ws.range(cell_addr).value = val
            apply_center(ws, cell_addr)

    # Ghi tên sản phẩm vào C4:D5
    ws.range("C4").value = data.product_name
    apply_center(ws, "C4:D5")

    # Ghi số PO vào I4:L5
    ws.range("I4").value = data.po_number
    apply_center(ws, "I4:L5")

    # Ghi ngày vào M4:N5
    formatted_date = datetime.strptime(data.date_code, "%Y%m%d").strftime("%Y.%m.%d")
    ws.range("M4").value = formatted_date
    apply_center(ws, "M4:N5")

    # Căn giữa toàn bộ vùng dữ liệu chính
    apply_center(ws, "B11:L15")

    wb.save(save_path)
    wb.close()
    app.quit()

    print(f"✅ Đã tạo file tại: {save_path}")

if __name__ == "__main__":
    main()
