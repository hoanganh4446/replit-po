import xlwings as xw
from datetime import datetime
import os
import random
import data

random.seed(datetime.now().timestamp())

# Cấu hình E → N (10 cột)
rand_config = [
    (7605, 8500, "div100"),   # E
    (6405, 6900, "div100"),   # F
    (18005, 19300, "div100"), # G
    (9005, 9300, "div100"),   # H
    (3130, 3200, False),      # I
    (905, 1065, False),       # J
    (1720, 1905, False),      # K
    (506, 550, False),        # L
    (5105, 5200, "div100"),   # M
    (4605, 4700, "div100")    # N
]

cols = list("EFGHIJKLMN")

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

    # ✅ Chèn ảnh nếu có
    if hasattr(data, "image_path") and os.path.exists(data.image_path):
        ws.pictures.add(data.image_path, left=ws.range("A1").left, top=ws.range("A1").top, width=150, height=40)

    # A11:A15 – số tem
    for i, sn in enumerate(data.serial_numbers):
        ws.range(f"A{11+i}").value = sn

    # E11:N15 – random
    for row in range(5):
        used = set()
        for col_idx, (a, b, mode) in enumerate(rand_config):
            while True:
                val = random.randint(min(a, b), max(a, b))
                if val not in used:
                    used.add(val)
                    break
            val = round(val / 100, 2) if mode == "div100" else val
            ws.range(f"{cols[col_idx]}{11+row}").value = val

    # C4:D5 – tên sản phẩm
    ws.range("C4").value = data.product_name
    apply_center(ws, "C4:D5")

    # H4:M5 – số PO
    ws.range("H4").value = data.po_number
    apply_center(ws, "H4:M5")

    # T4:W5 – ngày định dạng yyyy.mm.dd
    formatted_date = datetime.strptime(data.date_code, "%Y%m%d").strftime("%Y.%m.%d")
    ws.range("T4").value = formatted_date
    apply_center(ws, "T4:W5")

    # Căn giữa nội dung chính
    apply_center(ws, "A11:A15")
    apply_center(ws, "E11:N15")

    # Lưu và đóng
    wb.save(save_path)
    wb.close()
    app.quit()

    print(f"✅ File đã tạo: {save_path}")

if __name__ == "__main__":
    main()
