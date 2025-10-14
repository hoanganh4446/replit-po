import os
import random
from datetime import datetime
import xlwings as xw
import data

random.seed(datetime.now().timestamp())

# Cấu hình từng cột E → N
rand_config = [
    (7520, 8550, "div100"),    # E
    (6320, 6750, "div100"),    # F
    (2110, 2170, "div10"),     # G
    (8220, 9050, "div100"),    # H
    (3080, 3200, False),       # I
    (4120, 4790, "div10"),     # J
    (1860, 1940, False),       # K
    (3690, 4400, "div10"),     # L
    (5200, 5400, "div100"),    # M
    (4400, 4490, "div100")     # N
]

cols = list("EFGHIJKLMN")

def apply_center(ws, cell_range):
    rng = ws.range(cell_range)
    rng.api.HorizontalAlignment = -4108  # center
    rng.api.VerticalAlignment = -4108    # middle

def main():
    file_name = f"{data.product_name} - PO# {data.po_number}-{data.date_code.strip()}"
    today_str = datetime.today().strftime("%Y-%m-%d")
    output_dir = os.path.join(data.output_root, today_str, file_name)
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, f"{file_name}.xlsx")

    app = xw.App(visible=False)
    wb = app.books.open(data.template_file)
    ws = wb.sheets[0]

    # 1. Ghi tên sản phẩm vào C4:D5
    ws.range("C4").value = data.product_name
    ws.range("C4:D5").merge()
    apply_center(ws, "C4:D5")

    # 2. Ghi serial vào A11:A15
    for i, sn in enumerate(data.serial_numbers):
        cell = f"A{11+i}"
        ws.range(cell).value = sn
        apply_center(ws, cell)

    # 3. Random E11:N15
    for row in range(5):
        used = set()
        for col_idx, (a, b, mode) in enumerate(rand_config):
            while True:
                val = random.randint(min(a,b), max(a,b))
                if val not in used:
                    used.add(val)
                    break
            if mode == "div100":
                val = round(val / 100, 2)
            elif mode == "div10":
                val = round(val / 10, 1)
            ws.range(f"{cols[col_idx]}{11+row}").value = val
            apply_center(ws, f"{cols[col_idx]}{11+row}")

    # 4. Ghi số PO vào H4:M5
    try:
        ws.range("H4:M5").unmerge()
    except:
        pass
    ws.range("H4").value = data.po_number
    ws.range("H4:M5").merge()
    apply_center(ws, "H4:M5")

    # 5. Ghi ngày vào T4:W5 (yyyy.mm.dd)
    try:
        ws.range("T4:W5").unmerge()
    except:
        pass
    formatted_date = datetime.strptime(data.date_code.strip(), "%Y%m%d").strftime("%Y.%m.%d")
    ws.range("T4").value = formatted_date
    ws.range("T4:W5").merge()
    apply_center(ws, "T4:W5")

    # 6. Center toàn bộ dữ liệu
    apply_center(ws, "A11:A15")
    apply_center(ws, "E11:N15")

    wb.save(save_path)
    wb.close()
    app.quit()

    print(f"✅ File đã lưu tại:\n{save_path}")

if __name__ == "__main__":
    main()
