import os
import random
from datetime import datetime
import xlwings as xw
import data

random.seed(datetime.now().timestamp())

# Cấu hình từng cột từ E → K
rand_config = [
    (8400, 9500, "div100"),    # E
    (6100, 7400, "div100"),    # F
    (1980, 2100, "div10"),     # G
    (9000, 11000, "div100"),   # H
    (4200, 4400, False),       # I
    (5600, 5900, "div100"),    # J
    (4560, 5000, "div100")     # K
]

cols = list("EFGHIJK")

def apply_center(ws, cell_range):
    rng = ws.range(cell_range)
    rng.api.HorizontalAlignment = -4108  # center
    rng.api.VerticalAlignment = -4108    # middle

def main():
    file_name = f"{data.product_name} - PO# {data.po_number} - {data.date_code.strip()}"
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

    # 3. Ghi random vào E11:K15
    for row in range(5):
        used = set()
        for col_idx, (a, b, mode) in enumerate(rand_config):
            cell = f"{cols[col_idx]}{11+row}"
            while True:
                val = random.randint(min(a,b), max(a,b))
                if val not in used:
                    used.add(val)
                    break
            if mode == "div100":
                val = round(val / 100, 2)
            elif mode == "div10":
                val = round(val / 10, 1)
            ws.range(cell).value = val
            apply_center(ws, cell)

    # 4. Ghi số PO vào H4:J5 (merge tự động nếu lỗi)
    try:
        ws.range("H4:J5").unmerge()
    except:
        pass
    ws.range("H4").value = data.po_number
    ws.range("H4:J5").merge()
    apply_center(ws, "H4:J5")

    # 5. Ghi ngày tháng vào Q4:T5 (format yyyy.mm.dd)
    try:
        ws.range("Q4:T5").unmerge()
    except:
        pass
    formatted_date = datetime.strptime(data.date_code.strip(), "%Y%m%d").strftime("%Y.%m.%d")
    ws.range("Q4").value = formatted_date
    ws.range("Q4:T5").merge()
    apply_center(ws, "Q4:T5")

    # 6. Center toàn bộ vùng nhập
    apply_center(ws, "A11:A15")
    apply_center(ws, "E11:K15")

    wb.save(save_path)
    wb.close()
    app.quit()

    print(f"✅ Đã lưu thành công tại:\n{save_path}")

if __name__ == "__main__":
    main()
