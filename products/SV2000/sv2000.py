import os
import random
from datetime import datetime
import xlwings as xw
import data  # đảm bảo data.py chứa các biến cần thiết

random.seed(datetime.now().timestamp())

# RANDBETWEEN cấu hình theo F, G, E
rand_config = [
    (2550, 2680, False),      # F
    (2550, 2680, False),      # G
    (1260, 1470, "div100")    # E
]

cols = ['F', 'G', 'E'] # <-- THAY ĐỔI Ở ĐÂY

def apply_center(ws, cell_range):
    rng = ws.range(cell_range)
    rng.api.HorizontalAlignment = -4108  # xlCenter
    rng.api.VerticalAlignment = -4108    # xlCenter

def main():
    file_name = f"{data.product_name} - PO# {data.po_number} - {data.date_code.strip()}"
    today_str = datetime.today().strftime("%Y-%m-%d")
    output_path = os.path.join(data.output_root, today_str, file_name)
    os.makedirs(output_path, exist_ok=True)
    save_path = os.path.join(output_path, f"{file_name}.xlsx")

    app = xw.App(visible=False)
    wb = app.books.open(data.template_file)
    ws = wb.sheets[0]

    # 1. Ghi tên sản phẩm vào D3
    ws.range("D3").value = data.product_name
    apply_center(ws, "D3")

    # 2. Ghi serial vào B9:B13
    for i, sn in enumerate(data.serial_numbers):
        cell = f"B{9+i}"
        ws.range(cell).value = sn
        apply_center(ws, cell)

    # 3. Ghi random vào cột F, G, E (từ hàng 9 đến 13), mỗi hàng không trùng nhau # <-- COMMENT CẬP NHẬT
    for row in range(9, 14):
        used = set()
        for col_idx, (a, b, mode) in enumerate(rand_config):
            while True:
                val = random.randint(a, b)
                if val not in used:
                    used.add(val)
                    break
            if mode == "div100":
                val = round(val / 100, 2)
            cell = f"{cols[col_idx]}{row}" # Sử dụng cols đã cập nhật
            ws.range(cell).value = val
            apply_center(ws, cell)

    # 4. Ghi số PO vào F3:G3 (merge & center, không thêm 'PO#')
    try:
        ws.range("F3:G3").unmerge()
    except:
        pass
    ws.range("F3").value = data.po_number
    ws.range("F3:G3").merge()
    apply_center(ws, "F3:G3")

    # 5. Ghi ngày tháng vào M3:N3 (format YYYY.MM.DD)
    formatted_date = datetime.strptime(data.date_code.strip(), "%Y%m%d").strftime("%Y.%m.%d")
    ws.range("M3").value = formatted_date
    ws.range("M3:N3").merge()
    apply_center(ws, "M3:N3")

    # 6. Center toàn bộ vùng dữ liệu liên quan
    apply_center(ws, "A11:A15")
    # apply_center(ws, "F9:H13") # <-- DÒNG NÀY ĐÃ BỊ XÓA/VÔ HIỆU HÓA
                                # vì việc căn giữa từng ô đã được thực hiện ở mục 3
                                # và cột H không còn là cột random thứ 3.
                                # Các ô ở cột F, G, E đã được căn giữa riêng lẻ.

    # 7. Lưu file
    wb.save(save_path)
    wb.close()
    app.quit()

    print(f"✅ File đã lưu tại:\n{save_path}")

if __name__ == "__main__":
    main()