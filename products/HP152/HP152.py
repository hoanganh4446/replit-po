import xlwings as xw
from datetime import datetime
import os
import random
import data

random.seed(datetime.now().timestamp())

# Cấu hình các cột B → L (11 cột)
rand_config = [
    (890, 940, False),         # B
    (1120, 1180, False),       # C
    (1665, 1735, False),       # D
    (2010, 2080, False),       # E
    (2415, 2485, False),       # F
    (30, 47, "div100"),        # G
    (395, 523, "div100"),      # H
    (540, 735, "div100"),      # I
    (1020, 1286, "div100"),    # J
    (1365, 1658, "div100"),    # K
    (2388, 2604, "div100")     # L
]

cols = list("BCDEFGHIJKL")

def apply_center(ws, cell_range):
    """Căn giữa văn bản trong một phạm vi ô."""
    rng = ws.range(cell_range)
    rng.api.HorizontalAlignment = -4108  # xlCenter
    rng.api.VerticalAlignment = -4108    # xlCenter

def generate_unique_randoms(a, b, count):
    """Sinh số ngẫu nhiên không trùng."""
    result = set()
    while len(result) < count:
        result.add(random.randint(a, b))
    return list(result)

def main():
    """Hàm chính tạo file Excel."""
    # Tên file và thư mục
    file_name = f"{data.product_name} - PO#{data.po_number} - {data.date_code}"
    today_str = datetime.today().strftime("%Y-%m-%d")
    output_root = os.path.join(data.output_root, today_str)
    file_folder = os.path.join(output_root, file_name)
    os.makedirs(file_folder, exist_ok=True)
    save_path = os.path.join(file_folder, f"{file_name}.xlsx")

    # Mở ứng dụng Excel
    app = xw.App(visible=False)
    wb = app.books.open(data.template_file)
    ws = wb.sheets[0]

    # Ghi serial vào A11:A15
    for i, sn in enumerate(data.serial_numbers):
        cell = f"A{11+i}"
        ws.range(cell).value = sn
        apply_center(ws, cell)

    # Ghi random vào B11:L15 (không trùng trong từng hàng)
    for row in range(5):
        values = []
        for col_idx, (a, b, mode) in enumerate(rand_config):
            val = random.randint(a, b)
            if mode == "div100":
                val = round(val / 100, 2)
            values.append(val)
        for col_idx, val in enumerate(values):
            cell = f"{cols[col_idx]}{11+row}"
            ws.range(cell).value = val
            apply_center(ws, cell)

    # Ghi tên sản phẩm vào C4:D5
    ws.range("C4").value = data.product_name
    apply_center(ws, "C4:D5")

    # Ghi số PO vào I4:L5
    ws.range("I4").value = data.po_number
    apply_center(ws, "I4:L5")

    # Ghi ngày tháng vào M4:N5
    formatted_date = datetime.strptime(data.date_code, "%Y%m%d").strftime("%Y.%m.%d")
    ws.range("M4").value = formatted_date
    apply_center(ws, "M4:N5")

    # Căn giữa toàn bộ vùng dữ liệu chính
    apply_center(ws, "B11:L15")

    # Lưu và đóng
    wb.save(save_path)
    wb.close()
    app.quit()

    print(f"✅ Đã tạo file tại: {save_path}")

if __name__ == "__main__":
    main()
