import argparse
import re
from pathlib import Path

import pandas as pd


BARCODE_PATTERN = re.compile(r"^[A-Z]{3}PR\d{2}S\d{2}R\d{2}p\d{2}$")


def is_valid_barcode(value: str) -> bool:
    if value is None:
        return False
    return bool(BARCODE_PATTERN.fullmatch(str(value).strip()))


def validate_csv_barcodes(csv_path: str, barcode_column: str = "barcode", max_rows: int | None = None) -> int:
    df = pd.read_csv(csv_path)
    if max_rows is not None:
        df = df.head(int(max_rows))

    if barcode_column not in df.columns:
        raise ValueError(f"Column '{barcode_column}' not found in {csv_path}")

    invalid_rows = []
    for idx, barcode in df[barcode_column].items():
        if not is_valid_barcode(barcode):
            invalid_rows.append((idx + 1, barcode))

    if not invalid_rows:
        print(f"OK: all {len(df)} barcode values in '{barcode_column}' are valid.")
        return 0

    print(f"Found {len(invalid_rows)} invalid barcode value(s) in '{barcode_column}':")
    for row_num, barcode in invalid_rows[:50]:
        print(f"  row {row_num}: {barcode}")
    if len(invalid_rows) > 50:
        print(f"  ... and {len(invalid_rows) - 50} more")

    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate plate barcode format: <AAA>PR##S##R##p## (e.g. IMXPR01S04R01p06)."
    )
    parser.add_argument("--barcode", help="Validate a single barcode value")
    parser.add_argument("--csv", help="CSV file path for batch validation")
    parser.add_argument("--column", default="barcode", help="Barcode column name when using --csv")
    parser.add_argument("--max-rows", type=int, default=None, help="Optional limit for CSV validation")

    args = parser.parse_args()

    if args.barcode:
        if is_valid_barcode(args.barcode):
            print(f"OK: '{args.barcode}' is valid.")
            return 0
        print(f"INVALID: '{args.barcode}' does not match <AAA>PR##S##R##p##.")
        return 1

    if args.csv:
        csv_path = Path(args.csv)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV not found: {csv_path}")
        return validate_csv_barcodes(str(csv_path), args.column, args.max_rows)

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
