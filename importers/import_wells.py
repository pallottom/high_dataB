from sqlalchemy import column
from models import Well, specimen
import re



def _parse_wellkey(well_key: str):
    """
    Parse a well key into row and column.
    Accepts formats like A1, A01, A12, A_1, A-12, A 12, etc.
    Returns: (row, column)
    """
    rows_allowed = 'ABCDEFGHIJKLMNOP'
    max_col = 24

    # Normalize input: strip spaces, uppercase
    well_key = well_key.strip().upper()

    # Extract the letter and number, ignoring any characters in between
    match = re.match(r"^([A-P])[^0-9]*(\d{1,2})$", well_key)
    if not match:
        raise ValueError(f"Invalid well key format: '{well_key}'")

    row_letter, col_str = match.groups()
    row = rows_allowed.find(row_letter) + 1
    column = int(col_str)

    if column > max_col:
        raise ValueError(
            f"Column of well_key '{well_key}' must not be larger than {max_col}"
        )
    if row == 0:
        raise ValueError(
            f"Row of well_key '{well_key}' is invalid, must be one of {rows_allowed}"
        )
    
    normalized_well_key = f"{row_letter}{col_str.zfill(2)}"

    return str(row), str(column), str(normalized_well_key)



def import_well(session, plate, well_key, specimen, screen=None):
    """Get or create a Well, reusing parsing logic from create_well."""
    row, col, normalized_well_key = _parse_wellkey(well_key)  # parse to use in query

    well = session.query(Well).filter_by(
        well_key=normalized_well_key,
        col=col,
        row=row,
        plate=plate,
        specimen=specimen
    ).first()

    if not well:
        well = Well(
            well_key=normalized_well_key, 
            col=col, 
            row=row, 
            plate=plate, 
            specimen=specimen 
            ) 
        session.add(well)
        session.flush()
    elif well.specimen is None:
        well.specimen = specimen

    return well