import xlwings as xw
from datetime import datetime
import os
import random
import data

random.seed(datetime.now().timestamp())

# Cấu hình E → M
rand_config = [
    (1215, 1406, "div100"),   # E
    (1285, 1456, "div100"),   # F
    (520, 590, False),        # G
    (520, 590, False),        # H
    (2180, 2895, "div100"),   # I
    None,                    # ✅ J – giữ ký tự "/"
    (2215, 2806, "div100"),   # K
    (4415, 5406, "div100"),   # L
    (9252, 11856, "div100")   # M
]

cols = list("EFGHIJKLM")

def apply_center(ws, cell_range):
    rng = ws.range(cell_range)
    rng.api.HorizontalAlignment = -4108
    rng.api.VerticalAlignment = -4108

def main():
    file_name = f"{data.product_name} - PO#{data.po_number} - {data.date_code}"
    today_str = datetime.today().strftime("%Y-%m-%d")
    output_root = os.path.join(data.output_root, today_str)
    file_folder = os.path.join(output_root, file_name)
    os.makedirs(file_folder, exist_ok=True)
    save_path = os.path.join(file_folder, f"{file_name}.xlsx")

    app = xw.App(visible=False)
    wb = app.books.open(data.template_file)
    ws = wb.sheets[0]

    # Ghi serial A11:A15
    for i, sn in enumerate(data.serial_numbers):
        ws.range(f"A{11+i}").value = sn
        apply_center(ws, f"A{11+i}")

    # Ghi random E11:M15 (J = "/")
    for row in range(5):
        used = set()
        for col_idx, config in enumerate(rand_config):
            cell = f"{cols[col_idx]}{11+row}"
            if config is None:
                ws.range(cell).value = "/"
                apply_center(ws, cell)
                continue
            a, b, mode = config
            while True:
                val = random.randint(a, b)
                if val not in used:
                    used.add(val)
                    break
            val = round(val / 100, 2) if mode == "div100" else val
            ws.range(cell).value = val
            apply_center(ws, cell)

    # Ghi tên sản phẩm vào C4:E5
    ws.range("C4").value = data.product_name
    apply_center(ws, "C4:E5")

    # Ghi số PO vào F4:H5
    ws.range("F4").value = data.po_number
    apply_center(ws, "F4:H5")

    # Ghi ngày tháng vào R4:U5
    formatted_date = datetime.strptime(data.date_code, "%Y%m%d").strftime("%Y.%m.%d")
    ws.range("R4").value = formatted_date
    apply_center(ws, "R4:U5")

    wb.save(save_path)
    wb.close()
    app.quit()

    print(f"✅ File đã tạo: {save_path}")

if __name__ == "__main__":
    main()
