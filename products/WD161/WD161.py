import os
import random
from datetime import datetime
import xlwings as xw
import data

random.seed(datetime.now().timestamp())

rand_config = [
    (2100, 2799, "div100"), (2100, 2300, "div100"),
    (515, 600, False), (515, 600, False),
    (2200, 2399, "div100"), None,
    (2250, 2499, "div100"), (4623, 4800, "div100"),
    (11000, 11900, "div100")
]
cols = list("EFGHIJKLM")

def apply_center(ws, cell_range):
    rng = ws.range(cell_range)
    rng.api.HorizontalAlignment = -4108
    rng.api.VerticalAlignment = -4108

def main():
    file_name = f"{data.product_name} - PO#{data.po_number} - {data.date_code.strip()}"
    today_str = datetime.today().strftime("%Y-%m-%d")
    output_dir = os.path.join(data.output_root, today_str, file_name)
    os.makedirs(output_dir, exist_ok=True)
    save_path = os.path.join(output_dir, f"{file_name}.xlsx")

    if not os.path.exists(data.template_file):
        print(f"❌ Template không tồn tại: {data.template_file}")
        return

    with xw.App(visible=False) as app:
        wb = app.books.open(data.template_file)
        ws = wb.sheets[0]

        for i, sn in enumerate(data.serial_numbers):
            cell = f"A{11+i}"
            ws.range(cell).value = sn
            apply_center(ws, cell)

        for row in range(5):
            used = set()
            for col_idx, config in enumerate(rand_config):
                cell = f"{cols[col_idx]}{11 + row}"
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
                if mode == "div100":
                    val = round(val / 100, 2)
                ws.range(cell).value = val
                apply_center(ws, cell)

        ws.range("C4").value = data.product_name
        ws.range("C4:E5").merge()
        apply_center(ws, "C4:E5")

        ws.range("F4").value = data.po_number
        ws.range("F4:H5").merge()
        apply_center(ws, "F4:H5")

        formatted_date = datetime.strptime(data.date_code.strip(), "%Y%m%d").strftime("%Y.%m.%d")
        ws.range("R4").value = formatted_date
        ws.range("R4:U5").merge()
        apply_center(ws, "R4:U5")

        wb.save(save_path)

    print(f"✅ File đã lưu tại: {save_path}")

if __name__ == "__main__":
    main()
