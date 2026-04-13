from models import Specimen, HumanDonor, MouseDonor, Virus, Bacteria, CellType, CellCharacteristics, Anticoagulant 
from sqlalchemy.orm import Session
import json
from pathlib import Path


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


_PUBCHEM_HASH_BY_NAME = None


def _normalize_substance_name(name):
    return str(name).strip().lower()


def _load_pubchem_hashes():
    global _PUBCHEM_HASH_BY_NAME
    if _PUBCHEM_HASH_BY_NAME is not None:
        return _PUBCHEM_HASH_BY_NAME

    pubchem_path = Path(__file__).resolve().parent.parent / "pubchem_data.json"
    hash_by_name = {}
    try:
        with pubchem_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        for item in payload.get("results", []):
            common_name = item.get("common_name")
            hash_sha256_8 = item.get("hash_sha256_8")
            if not hash_sha256_8:
                continue

            hash_value = str(hash_sha256_8)

            if common_name:
                hash_by_name[_normalize_substance_name(common_name)] = hash_value

            synonyms = item.get("depositor-supplied-synonyms") or []
            if isinstance(synonyms, list):
                for synonym in synonyms:
                    if synonym and isinstance(synonym, str):
                        hash_by_name.setdefault(_normalize_substance_name(synonym), hash_value)
    except (OSError, ValueError, TypeError):
        hash_by_name = {}

    _PUBCHEM_HASH_BY_NAME = hash_by_name
    return _PUBCHEM_HASH_BY_NAME


def import_anticoagulant(session: Session, anticoagulant_name):
    anticoagulant_name = _none_if_missing(anticoagulant_name)
    if anticoagulant_name is None:
        return None

    name = str(anticoagulant_name).strip()
    if not name or name.lower() == "nan":
        return None

    pubchem_hashes = _load_pubchem_hashes()
    anticoagulant_hash = pubchem_hashes.get(_normalize_substance_name(name))

    # If not found in PubChem, store a non-hash marker.
    if not anticoagulant_hash:
        anticoagulant_hash = "non available"

    if anticoagulant_hash == "non available":
        anticoagulant = (
            session.query(Anticoagulant)
            .filter_by(hash=anticoagulant_hash, anticoagulant_name=name)
            .first()
        )
    else:
        anticoagulant = (
            session.query(Anticoagulant)
            .filter_by(hash=anticoagulant_hash)
            .first()
        )
    if not anticoagulant:
        anticoagulant = Anticoagulant(hash=anticoagulant_hash, anticoagulant_name=name)
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
            specimen.anticoagulant = anticoagulant
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
                anticoagulant=anticoagulant,
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
            specimen.anticoagulant = anticoagulant
        if not specimen:
            specimen = MouseDonor(
                name=_to_optional_str(row.get("donor_ID")) or "unknown",#donor_name,
                strain=_to_optional_str(row.get("strain")) or "C57BL/6",
                transgene=_to_optional_str(row.get("transgene")),
                anticoagulant=anticoagulant,
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


