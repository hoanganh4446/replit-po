import xlwings as xw
from datetime import datetime
import os
import random
import data

random.seed(datetime.now().timestamp())

def apply_center(sheet, cell_range):
    rng = sheet.range(cell_range)
    rng.api.HorizontalAlignment = -4108  # Center
    rng.api.VerticalAlignment = -4108    # Middle

def main():
    product_name = data.product_name
    po_number = data.po_number
    date_code = data.date_code

    file_name = f"{product_name} - PO#{po_number} - {date_code}"
    today_str = datetime.today().strftime("%Y-%m-%d")
    output_root = os.path.join(data.output_root, f"{today_str}")
    file_folder = os.path.join(output_root, file_name)
    os.makedirs(file_folder, exist_ok=True)
    save_path = os.path.join(file_folder, f"{file_name}.xlsx")

    app = xw.App(visible=False)
    wb = app.books.open(data.template_file)
    ws = wb.sheets[0]

    # B3 – Tên sản phẩm
    ws.range("B3").value = product_name
    apply_center(ws, "B3")

    # G3 – Số PO (bỏ chữ PO#)
    if ws.range("G3").merge_cells:
        ws.range("G3").unmerge()
    ws.range("G3").value = po_number
    apply_center(ws, "G3")

    # S3 – Ngày (yyyy.mm.dd)
    if ws.range("S3").merge_cells:
        ws.range("S3").unmerge()
    formatted_date = datetime.strptime(date_code, "%Y%m%d").strftime("%Y.%m.%d")
    ws.range("S3").value = formatted_date
    apply_center(ws, "S3")

    # A8:A12 – Ghi số tem
    for i, serial in enumerate(data.serial_numbers): # Giả định data.serial_numbers có 5 phần tử
        cell = f"A{8 + i}"
        ws.range(cell).value = serial
        apply_center(ws, cell)

    # B8:T12 – Sinh dữ liệu ngẫu nhiên và cố định cho các cột từ B đến T
    rand_config = [
        (1522, 1633, False),      # B - số
        (None, None, "/"),        # C - /
        (None, None, "/"),        # D - /
        (None, None, "/"),        # E - /
        (None, None, "/"),        # F - /
        (3290, 3370, "div100"),    # G - số /100
        (None, None, "/"),        # H - /
        (None, None, "/"),        # I - /
        (None, None, "/"),        # J - /
        (None, None, "OK"),       # K - OK
        (None, None, "/"),        # L - /
        (None, None, "/"),        # M - /
        (None, None, "/"),        # N - /
        (None, None, "/"),        # O - /
        (None, None, "/"),        # P - /
        (None, None, "/"),        # Q - /
        (None, None, "/"),        # R - /
        (None, None, "/"),        # S - /
        (10150, 10500, "div100")   # T - số /100 (comment đã sửa cho rõ)
    ]

    used_rows = set() # Đảm bảo mỗi hàng dữ liệu (B đến T) là duy nhất
    while len(used_rows) < 5: # Sinh 5 hàng dữ liệu
        current_row_values = []
        # Set này dùng để đảm bảo các số ngẫu nhiên *gốc* (trước khi chia 100) là duy nhất *trong cùng một hàng*
        # đối với các cột được cấu hình sinh số.
        used_numbers_in_current_row = set()

        for col_idx, (min_val, max_val, mode_or_fixed_value) in enumerate(rand_config):
            cell_val = None
            if min_val is None and max_val is None: # Đây là giá trị cố định (ví dụ: "/", "OK")
                cell_val = mode_or_fixed_value
            else: # Đây là trường hợp sinh số ngẫu nhiên
                if not (isinstance(min_val, int) and isinstance(max_val, int)):
                    raise ValueError(f"Cấu hình không hợp lệ cho sinh số ngẫu nhiên ở vị trí {col_idx}: ({min_val}, {max_val})")

                # Sinh số ngẫu nhiên gốc và đảm bảo nó là duy nhất trong hàng này
                # cho các cột sinh số.
                while True:
                    generated_int = random.randint(min_val, max_val)
                    if generated_int not in used_numbers_in_current_row:
                        used_numbers_in_current_row.add(generated_int)
                        cell_val = generated_int # Giá trị ban đầu là số nguyên vừa sinh
                        break
                
                # Áp dụng phép chia nếu mode là "div100"
                if mode_or_fixed_value == "div100":
                    cell_val = round(cell_val / 100.0, 2)
                # Nếu mode_or_fixed_value là False, cell_val giữ nguyên là generated_int

            current_row_values.append(cell_val)
        
        row_tuple = tuple(current_row_values)
        if row_tuple not in used_rows:
            used_rows.add(row_tuple)

    # Ghi 5 hàng dữ liệu đã sinh ra vào Excel từ B8
    for i, row_data in enumerate(used_rows):
        for j, val_to_write in enumerate(row_data):
            # (8+i) là dòng (8, 9, ..., 12)
            # (2+j) là cột (B=2, C=3, ..., T=20)
            cell_obj = ws.range((8 + i, 2 + j))
            cell_obj.value = val_to_write
            apply_center(ws, cell_obj) # Truyền thẳng đối tượng cell để căn giữa

    wb.save(save_path)
    wb.close()
    app.quit()

    print(f"✅ Đã tạo file tại: {save_path}")

if __name__ == "__main__":
    main()