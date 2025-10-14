import os
import datetime
from random import randint
import xlwings as xw
from data import TEMPLATE_FILE, OUTPUT_ROOT, PRODUCT_NAME, PO_NUMBER, PO_DATE, STICKERS

def generate_unique_row():
    while True:
        row = [
            round(randint(8712, 8950) / 100, 2),
            round(randint(2315, 2750) / 100, 2),
            randint(1290, 1340),
            randint(2350, 2580),
            round(randint(3210, 3500) / 100, 2)
        ]
        if len(set(row)) == len(row):
            return row

def apply_center(sheet, cell_range):
    rng = sheet.range(cell_range)
    rng.api.HorizontalAlignment = -4108  # center
    rng.api.VerticalAlignment = -4108    # middle

def main():
    file_name = f"{PRODUCT_NAME} - PO#{PO_NUMBER} - {PO_DATE}"
    today_str = datetime.datetime.today().strftime("%Y-%m-%d")

    # ✅ Tạo đúng cấu trúc thư mục
    full_output_path = os.path.join(OUTPUT_ROOT, today_str, file_name)
    os.makedirs(full_output_path, exist_ok=True)
    save_path = os.path.join(full_output_path, f"{file_name}.xlsx")

    app = xw.App(visible=False)
    wb = app.books.open(TEMPLATE_FILE)
    ws = wb.sheets[0]

    # ✅ Ghi thêm PRODUCT_NAME vào B3:C3
    ws.range("B3").value = PRODUCT_NAME
    ws.range("B3:C3").merge()
    apply_center(ws, "B3:C3")

    # Ghi số tem vào B9:B13
    for i in range(5):
        cell = f"B{9+i}"
        ws.range(cell).value = STICKERS[i]
        apply_center(ws, cell)

    # Ghi dữ liệu random D9:H13
    for i in range(5):
        values = generate_unique_row()
        for j in range(5):  # D → H là cột 4–8
            cell = f"{chr(68+j)}{9+i}"  # D = 68
            ws.range(cell).value = values[j]
            apply_center(ws, cell)

    # Ghi PO vào E3 (merge E3:F3)
    ws.range("E3").value = PO_NUMBER
    ws.range("E3:F3").merge()
    apply_center(ws, "E3:F3")

    # Ghi ngày định dạng yyyy.mm.dd vào I3 (merge I3:J3)
    formatted_date = f"{PO_DATE[:4]}.{PO_DATE[4:6]}.{PO_DATE[6:]}"
    ws.range("I3").value = formatted_date
    ws.range("I3:J3").merge()
    apply_center(ws, "I3:J3")

    # Lưu
    wb.save(save_path)
    wb.close()
    app.quit()

    print(f"✅ File saved: {save_path}")

if __name__ == "__main__":
    main()
