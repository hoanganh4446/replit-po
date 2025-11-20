import os
import random
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple

import xlwings as xw

import data

random.seed(datetime.now().timestamp())

ROWS = list(range(11, 16))
ALL_RANDOM_COLUMNS = [
    ("B", (24, 30, "div100")),
    ("C", (525, 550, "div100")),
    ("D", (811, 849, "div100")),
    ("E", (1019, 1055, "div100")),
    ("F", (1231, 1279, "div100")),
    ("G", (1515, 1585, "div100")),
    ("H", (2015, 2120, "div100")),
    ("I", (2610, 2760, "div100")),
    ("J", (3900, 4050, "div100")),
    ("K", (4520, 4699, "div100")),
    ("L", (5520, 5590, "div100")),
    ("M", (8550, 8700, "div100")),
    ("R", (1829, 1832, None)),
    ("S", (3, 9, "div10")),
]

SINGLE_ROW_RANDOM_COLUMNS = [
    ("P", (1851, 1999, None), None),
    ("Q", (24, 27, "div10"), None),
]

DEFAULT_INACTIVE_VALUE = "N/A"

COLUMN_SUFFIXES = {
    "R": "mm",
}


def apply_center(sheet: xw.main.Sheet, cell_range: str) -> None:
    rng = sheet.range(cell_range)
    rng.api.HorizontalAlignment = -4108  # center
    rng.api.VerticalAlignment = -4108  # middle


def transform_value(raw_val: int, mode: Optional[str]) -> float | int:
    if mode == "div100":
        return round(raw_val / 100, 2)
    if mode == "div10":
        return round(raw_val / 10, 1)
    return raw_val


def generate_unique_random(
    minimum: int,
    maximum: int,
    mode: Optional[str],
    used: set[int],
) -> float | int:
    if minimum > maximum:
        raise ValueError(f"Khoảng giá trị không hợp lệ: min={minimum} > max={maximum}")

    attempts = 0
    while True:
        raw_val = random.randint(minimum, maximum)
        attempts += 1
        if raw_val not in used or attempts > (maximum - minimum + 1):
            used.add(raw_val)
            return transform_value(raw_val, mode)


def generate_random_value(
    minimum: int,
    maximum: int,
    mode: Optional[str],
) -> float | int:
    if minimum > maximum:
        raise ValueError(f"Khoảng giá trị không hợp lệ: min={minimum} > max={maximum}")
    raw_val = random.randint(minimum, maximum)
    return transform_value(raw_val, mode)


def validate_config(sequence: Sequence[str], name: str, expected_len: int) -> None:
    if len(sequence) < expected_len:
        raise ValueError(
            f"{name} cần ít nhất {expected_len} phần tử, hiện tại chỉ có {len(sequence)}."
        )
    missing = [idx for idx, value in enumerate(sequence[:expected_len], start=1) if not value]
    if missing:
        raise ValueError(
            f"{name} có phần tử rỗng tại vị trí: {', '.join(map(str, missing))}."
        )


def validate_inputs(expected_rows: int) -> Path:
    validate_config(data.serial_numbers, "serial_numbers", expected_rows)
    validate_config(data.gross_weights, "gross_weights", expected_rows)
    validate_config(data.net_weights, "net_weights", expected_rows)

    template_path = Path(data.template_file)
    if not template_path.exists():
        raise FileNotFoundError(f"Không tìm thấy template: {template_path}")

    try:
        datetime.strptime(data.date_code, "%Y%m%d")
    except ValueError as exc:
        raise ValueError(
            f"date_code phải có định dạng YYYYMMDD, giá trị hiện tại: {data.date_code}"
        ) from exc

    return template_path


def center_range(ws: xw.main.Sheet, cell: str) -> None:
    apply_center(ws, cell)


def write_header(ws: xw.main.Sheet) -> None:
    ws.range("D4:F5").merge()
    ws.range("D4").value = data.product_name
    center_range(ws, "D4:F5")

    ws.range("I4:J5").merge()
    ws.range("I4").value = data.po_number
    center_range(ws, "I4:J5")

    ws.range("Q4:S5").merge()
    formatted_date = datetime.strptime(data.date_code, "%Y%m%d").strftime("%Y.%m.%d")
    ws.range("Q4").value = formatted_date
    center_range(ws, "Q4:S5")


def write_column_values(
    ws: xw.main.Sheet,
    column: str,
    values: Iterable[str | float | int],
) -> None:
    for offset, value in enumerate(values):
        cell = f"{column}{ROWS[offset]}"
        ws.range(cell).value = value
        center_range(ws, cell)


def fill_serials_and_weights(ws: xw.main.Sheet) -> None:
    write_column_values(ws, "A", data.serial_numbers[: len(ROWS)])
    write_column_values(ws, "N", data.gross_weights[: len(ROWS)])
    write_column_values(ws, "O", data.net_weights[: len(ROWS)])


def fill_random_blocks(ws: xw.main.Sheet) -> None:
    for excel_row in ROWS:
        used_values: set[int] = set()
        for column, config in ALL_RANDOM_COLUMNS:
            min_val, max_val, mode = config
            value = generate_unique_random(min_val, max_val, mode, used_values)
            suffix = COLUMN_SUFFIXES.get(column)
            if suffix:
                display_value = f"{int(value)}{suffix}"
            else:
                display_value = value
            cell = f"{column}{excel_row}"
            ws.range(cell).value = display_value
            center_range(ws, cell)


def fill_single_row_columns(ws: xw.main.Sheet) -> None:
    for column, config, suffix in SINGLE_ROW_RANDOM_COLUMNS:
        min_val, max_val, mode = config
        value = generate_random_value(min_val, max_val, mode)
        if suffix:
            display_value = f"{int(value)}{suffix}"
        else:
            display_value = value

        active_cell = f"{column}{ROWS[0]}"
        ws.range(active_cell).value = display_value
        center_range(ws, active_cell)

        for inactive_row in ROWS[1:]:
            inactive_cell = f"{column}{inactive_row}"
            ws.range(inactive_cell).value = DEFAULT_INACTIVE_VALUE
            center_range(ws, inactive_cell)


def ensure_output_directory() -> Tuple[Path, Path]:
    file_name = f"{data.product_name} - PO#{data.po_number} - {data.date_code}"
    today_folder = datetime.today().strftime("%Y-%m-%d")
    output_root = Path(data.output_root) / today_folder
    file_folder = output_root / file_name
    file_folder.mkdir(parents=True, exist_ok=True)
    return file_folder, file_folder / f"{file_name}.xlsx"


def main() -> None:
    template_path = validate_inputs(len(ROWS))
    file_folder, save_path = ensure_output_directory()

    app: Optional[xw.App] = None
    try:
        app = xw.App(visible=False)
        wb = app.books.open(str(template_path))
        ws = wb.sheets[0]

        fill_serials_and_weights(ws)
        fill_random_blocks(ws)
        fill_single_row_columns(ws)
        write_header(ws)

        wb.save(str(save_path))
        wb.close()
    finally:
        if app is not None:
            app.quit()

    print(f"✅ Đã tạo file tại: {save_path}")


if __name__ == "__main__":
    main()
