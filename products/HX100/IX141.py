import xlwings as xw
from datetime import datetime
import os
import random
import data

random.seed(datetime.now().timestamp())

def apply_center(sheet, cell_range):
    """Căn giữa văn bản trong một phạm vi ô."""
    rng = sheet.range(cell_range)
    rng.api.HorizontalAlignment = -4108  # xlCenter
    rng.api.VerticalAlignment = -4108    # xlCenter

def main():
    """Hàm chính tạo file Excel."""
    # Tên file và thư mục
    file_basename = f"{data.product_name} - PO# {data.po_number} - {data.date_str}"
    today_str = datetime.today().strftime("%Y-%m-%d")
    output_dir = os.path.join(data.output_root, today_str, file_basename)
    output_path = os.path.join(output_dir, f"{file_basename}.xlsx")

    # Tạo thư mục nếu chưa có
    os.makedirs(output_dir, exist_ok=True)

    # Mở file template bằng xlwings
    app = xw.App(visible=False)
    wb = app.books.open(data.template_path)

    # Ghi dữ liệu vào file
    ws = wb.sheets[0]

    # Ghi serial vào A11:A15
    for i, sn in enumerate(data.serials):
        rng = ws.range(f"A{11+i}")
        rng.value = sn
        apply_center(ws, f"A{11+i}")

    # Random dữ liệu vào F+G (merge), H+I (merge) dòng 11–15
    for row in range(11, 16):
        val_fg = round(random.randint(2130, 2240) / 100, 2)  # F+G
        val_hi = random.randint(7890, 8450)                  # H+I

        # F+G
        ws.range(f"F{row}").value = val_fg
        apply_center(ws, f"F{row}:G{row}")

        # H+I
        ws.range(f"H{row}").value = val_hi
        apply_center(ws, f"H{row}:I{row}")

    # Ghi PO vào F4 (merge F4:I4)
    ws.range("F4").value = data.po_number
    apply_center(ws, "F4:I4")

    # Ghi ngày vào Q4 (merge Q4:T4)
    formatted_date = f"{data.date_str[:4]}.{data.date_str[4:6]}.{data.date_str[6:]}"
    ws.range("Q4").value = formatted_date
    apply_center(ws, "Q4:T4")

    # Ghi tên sản phẩm vào C4 (merge C4:E5)
    ws.range("C4").value = data.product_name
    apply_center(ws, "C4:E5")

    # Lưu và đóng file
    wb.save(output_path)
    wb.close()
    app.quit()

    print(f"✅ Đã tạo file thành công:\n{output_path}")

if __name__ == "__main__":
    main()
