import xlwings as xw
from datetime import datetime
import os
import random
import data

random.seed(datetime.now().timestamp())

# B → K: 10 cột
rand_config = [
    (360, 380, False),         # B
    (560, 585, False),         # C
    (820, 840, False),         # D
    (1060, 1110, False),       # E
    (1280, 1300, False),       # F
    (1470, 1490, False),       # G
    (1490, 1550, "div100"),    # H
    (2320, 2390, "div100"),    # I
    (980, 1072, False),        # J
    (450, 470, "div100")       # K
]

cols = list("BCDEFGHIJK")

def generate_unique_randoms(a, b, count):
    result = set()
    while len(result) < count:
        result.add(random.randint(a, b))
    return list(result)

def apply_center(sheet, cell_range):
    rng = sheet.range(cell_range)
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

    # Ghi Serial A11:A15
    for i, sn in enumerate(data.serial_numbers):
        ws.range(f"A{11+i}").value = sn

    # Ghi random B11:K15
    for row in range(5):
        used = set()
        for col_idx, (a, b, mode) in enumerate(rand_config):
            while True:
                val = random.randint(a, b)
                if val not in used:
                    used.add(val)
                    break
            final_val = round(val / 100, 2) if mode == "div100" else val
            ws.range(f"{cols[col_idx]}{11+row}").value = final_val

    # Ghi tên sản phẩm tại B4:B5 (chỉ cần ô trên)
    ws.range("B4").value = data.product_name
    apply_center(ws, "B4:B5")

    # Ghi số PO tại E4:F5
    ws.range("E4").value = data.po_number
    apply_center(ws, "E4:F5")

    # Ghi ngày tại K4:L5
    formatted_date = datetime.strptime(data.date_code, "%Y%m%d").strftime("%Y.%m.%d")
    ws.range("K4").value = formatted_date
    apply_center(ws, "K4:L5")

    # Căn giữa dữ liệu chính
    apply_center(ws, "A11:A15")
    apply_center(ws, "B11:K15")

    wb.save(save_path)
    wb.close()
    app.quit()

    print(f"✅ Đã tạo file tại: {save_path}")

if __name__ == "__main__":
    main()
