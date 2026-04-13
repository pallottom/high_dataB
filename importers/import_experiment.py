from models import ConditionClass, Condition, Substance, Treatment, Experiment
import pandas as pd
import json
from pathlib import Path


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
                        # Keep first mapping for ambiguous synonyms shared by multiple compounds.
                        hash_by_name.setdefault(_normalize_substance_name(synonym), hash_value)
    except (OSError, ValueError, TypeError):
        hash_by_name = {}

    _PUBCHEM_HASH_BY_NAME = hash_by_name
    return _PUBCHEM_HASH_BY_NAME


def import_condition_class(session, name, description=None):
    """Get or create a ConditionClass by name."""
    cc = session.query(ConditionClass).filter_by(name=name).first()
    if not cc:
        cc = ConditionClass(
            name=name,
            description=description or f"Condition class for {name}"
        )
        session.add(cc)
        session.flush()
    return cc


def import_condition(session, condition_class):
    """Get or create a Condition for a given ConditionClass."""
    condition = session.query(Condition).filter_by(conditionclass_id=condition_class.id).first()
    if not condition:
        condition = Condition(conditionclass=condition_class)
        session.add(condition)
        session.flush()
    return condition


def import_substance(session, name, type="small_molecule", vendor="default_vendor"):
    """Get or create a Substance by name."""
    if not name or not pd.notna(name):
        return None

    name_str = str(name)
    pubchem_hashes = _load_pubchem_hashes()
    substance_hash = pubchem_hashes.get(_normalize_substance_name(name_str))

    # If not found in PubChem, store a non-hash marker.
    if not substance_hash:
        substance_hash = "not available"

    substance = session.query(Substance).filter_by(hash=substance_hash).first()
    if not substance:
        substance = Substance(
            hash=substance_hash,
            name=name_str,
            type=type,
            catalog_id=f"CAT_{name}",
            vendor=vendor,
            lot=f"LOT_{name}"
        )
        session.add(substance)
        session.flush()
    return substance


def import_treatment(session, condition, position, treatment_type,
                     substance, concentration=0, concentration_unit="nM", duration_min=0):
    if not substance:
        return None

    duration_str = f"{duration_min} minutes"  ## Option to add datetime# 

    existing = session.query(Treatment).filter(  # was filter_by
        Treatment.type == treatment_type,
        Treatment.substance_id == substance.id,
        Treatment.concentration == concentration,
        Treatment.concentration_unit == concentration_unit,
        Treatment.duration == duration_str,
        Treatment.condition_id == condition.id,  # Changed from 'condition' to 'condition_id'
        Treatment.position == position
    ).first()

    if existing:
        return existing

    treatment = Treatment(
        type=treatment_type,
        substance_id=substance.id,
        concentration=concentration,
        concentration_unit=concentration_unit,
        duration=duration_str,
        condition_id=condition.id,
        position=position
    )
    session.add(treatment)
    return treatment


def import_experiment(session, row, well, measurement):
    """
    Orchestrates ConditionClass, Condition, Substances, Treatments, Experiment creation.
    row = pandas row with input data.
    """
    # --- ConditionClass ---
    condition_class_name = row.get("condition_class", "default_condition_class")
    condition_class = import_condition_class(session, condition_class_name)

    # --- Condition ---
    condition = import_condition(session, condition_class)

    # --- Substances ---
    prim_substance = import_substance(session, row.get("prim_name"))
    activ_substance = import_substance(session, row.get("activ_name"))

    # --- Treatments ---
    if prim_substance:
        import_treatment(
            session,
            condition,
            position=0,
            treatment_type="primary",
            substance=prim_substance,
            concentration=row.get("prim_conc", 0),
            concentration_unit=row.get("prim_conc_unit", "nM"),
            duration_min=row.get("prim_time_min", 0),
        )

    if activ_substance:
        import_treatment(
            session,
            condition,
            position=1,
            treatment_type="activator",
            substance=activ_substance,
            concentration=row.get("activ_conc", 0),
            concentration_unit=row.get("activ_conc_unit", "nM"),
            duration_min=row.get("activ_time_min", 0),
        )

    # --- Experiment ---
    experiment = session.query(Experiment).filter_by(
        well_id=well.id, 
        condition_id=condition.id
        ).first()
    
    if not experiment:
        htrf_data_il1b = row.get("htrf_il1b_data")
        htrf_data_tnfa = row.get("htrf_tnfa_data")
        qc_status = "pass" if (pd.notna(htrf_data_il1b) or pd.notna(htrf_data_tnfa)) else "fail"

        experiment = Experiment(
            well_id=well.id,
            condition_id=condition.id,
            #measurement_id=measurement.id,
            qc=qc_status
        )
        session.add(experiment)
    return experiment
