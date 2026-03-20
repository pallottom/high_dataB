from models import Specimen, HumanDonor, MouseDonor, Virus, Bacteria, CellType, CellCharacteristics, Anticoagulat 
from sqlalchemy.orm import Session


def _none_if_missing(value):
    if value is None:
        return None
    try:
        if value != value:
            return None
    except Exception:
        pass

    text = str(value).strip()
    if text == "" or text.lower() == "nan":
        return None

    return value


def _to_optional_int(value):
    value = _none_if_missing(value)
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _to_optional_str(value):
    value = _none_if_missing(value)
    if value is None:
        return None
    return str(value).strip()


def _parse_binary(value):
    value = _none_if_missing(value)
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "t", "yes", "y"}:
        return True
    if text in {"0", "false", "f", "no", "n"}:
        return False
    return None


def import_anticoagulant(session: Session, anticoagulant_name):
    anticoagulant_name = _none_if_missing(anticoagulant_name)
    if anticoagulant_name is None:
        return None

    name = str(anticoagulant_name).strip()
    if not name or name.lower() == "nan":
        return None

    anticoagulant = (
        session.query(Anticoagulat)
        .filter_by(anticoagulant_name=name)
        .first()
    )
    if not anticoagulant:
        anticoagulant = Anticoagulat(anticoagulant_name=name)
        session.add(anticoagulant)
        session.flush()

    return anticoagulant


def import_specimen(session: Session, row: dict):
    """
    Import or retrieve a specimen (human or mouse donor) from a CSV row.
    Uses single-table inheritance through Specimen base.
    """

    # --- Determine donor type ---
    donor_type_raw = row.get("specimen", row.get("donor_species", "human"))
    donor_type = str(donor_type_raw).strip().lower() if donor_type_raw is not None else "human"
    if donor_type in {"", "nan", "none"}:
        donor_type = "human"
    donor_name = _to_optional_str(row.get("donor_loc")) or "Unknown"

    cell_type = None
    cell_char = None
    anticoagulant = None

    if donor_type in {"human", "mouse"}:
        # --- Cell type and characteristics ---
        cell_type_name = _to_optional_str(row.get("cell_type")) or "PBMC" # PBMC, Liver, Neuron, etc.
        cell_char_name = _to_optional_str(row.get("cell_characteristic")) or "Primary" # Primary, Culture, Mixed
        anticoagulant = import_anticoagulant(session, row.get("anticoagulant"))

        # Get or create cell type
        cell_type = (
            session.query(CellType)
            .filter_by(name=cell_type_name)
            .first()
        )
        if not cell_type:
            cell_type = CellType(name=cell_type_name)
            session.add(cell_type)
            session.flush()

        # Get or create cell characteristic
        cell_char = (
            session.query(CellCharacteristics)
            .filter_by(name=cell_char_name)
            .first()
        )
        if not cell_char:
            cell_char = CellCharacteristics(name=cell_char_name)
            session.add(cell_char)
            session.flush()

    # --- Create or retrieve specimen ---
    if donor_type == "human":
        specimen = (
            session.query(HumanDonor)
            .filter_by(name=donor_name)
            .first()
        )
        if specimen:
            specimen.anticoagulat = anticoagulant
        if not specimen:
            specimen = HumanDonor(
                name=donor_name,
                weight_kg=_none_if_missing(row.get("weight_kg")),
                height_cm=_none_if_missing(row.get("height_cm")),
                smoker=_parse_binary(row.get("smoker")),
                ethnicity=_to_optional_str(row.get("ethnicity")),
                blood_type=_to_optional_str(row.get("blood_type")),
                age=_to_optional_int(row.get("age")),
                sex=_to_optional_str(row.get("sex")),
                anticoagulat=anticoagulant,
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
        if specimen:
            specimen.anticoagulat = anticoagulant
        if not specimen:
            specimen = MouseDonor(
                name=_to_optional_str(row.get("donor_ID")) or "unknown",#donor_name,
                strain=_to_optional_str(row.get("strain")) or "C57BL/6",
                transgene=_to_optional_str(row.get("transgene")),
                anticoagulat=anticoagulant,
                cell_type=cell_type,
                cell_characteristic=cell_char,
            )
            session.add(specimen)
            session.flush()

    elif donor_type == "bacteria":
        specimen = (
            session.query(Bacteria)
            .filter_by(name=donor_name)
            .first()
        )
        if not specimen:
            specimen = Bacteria(
                name=donor_name,
                category_type=_to_optional_str(row.get("bacteria_type")) or _to_optional_str(row.get("type")) or "unknown",
            )
            session.add(specimen)
            session.flush()

    elif donor_type == "virus":
        specimen = (
            session.query(Virus)
            .filter_by(name=donor_name)
            .first()
        )
        if not specimen:
            specimen = Virus(
                name=donor_name,
                category_type=_to_optional_str(row.get("virus_type")) or _to_optional_str(row.get("type")) or "unknown",
            )
            session.add(specimen)
            session.flush()

    else:
        raise ValueError(f"Unknown donor_type: {donor_type}")

    return specimen
