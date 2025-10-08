from models import Specimen, HumanDonor, MouseDonor, CellType, CellCharacteristics 
from sqlalchemy.orm import Session


def import_specimen(session: Session, row: dict):
    """
    Import or retrieve a specimen (human or mouse donor) from a CSV row.
    Uses single-table inheritance through Specimen base.
    """

    # --- Determine donor type ---
    donor_type = row.get("donor_type", "human").lower().strip()  # fallback to human
    donor_name = row.get("donor_loc") or "Unknown"

    # --- Cell type and characteristics ---
    cell_type_name = row.get("cell_type", "PBMC") # PBMC, Liver, Neuron, etc.
    cell_char_name = row.get("cell_characteristic", "Primary") # Primary, Culture, Mixed

    # Get or create cell type
    cell_type = (
        session.query(CellType)
        .filter_by(cell_type_name=cell_type_name)
        .first()
    )
    if not cell_type:
        cell_type = CellType(cell_type_name=cell_type_name)
        session.add(cell_type)
        session.flush()

    # Get or create cell characteristic
    cell_char = (
        session.query(CellCharacteristics)
        .filter_by(characteristic_name=cell_char_name)
        .first()
    )
    if not cell_char:
        cell_char = CellCharacteristics(characteristic_name=cell_char_name)
        session.add(cell_char)
        session.flush()

    # --- Create or retrieve specimen ---
    if donor_type == "human":
        specimen = (
            session.query(HumanDonor)
            .filter_by(human_name=donor_name)
            .first()
        )
        if not specimen:
            specimen = HumanDonor(
                human_name=donor_name,
                age=row.get("age"),
                sex=row.get("sex"),
                cell_type=cell_type,
                cell_characteristic=cell_char,
            )
            session.add(specimen)
            session.flush()

    elif donor_type == "mouse":
        specimen = (
            session.query(MouseDonor)
            .filter_by(name=donor_name)
            .first()
        )
        if not specimen:
            specimen = MouseDonor(
                name=donor_name,
                strain=row.get("strain", "C57BL/6"),
                transgene=row.get("transgene"),
                cell_type=cell_type,
                cell_characteristic=cell_char,
            )
            session.add(specimen)
            session.flush()

    else:
        raise ValueError(f"Unknown donor_type: {donor_type}")

    return specimen
