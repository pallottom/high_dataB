import pandas as pd
from models import Measurement, Tnfa, Il1b
from sqlalchemy.orm import Session


def _to_float(value):
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def _import_il1b(session: Session, well, row: dict):
    il1b_measurement = (
        session.query(Il1b)
        .filter(Il1b.well_id == well.id)
        .first()
    )

    il1b_values = {
        "Em616": _to_float(row.get("Em616_IL1b")),
        "Em655": _to_float(row.get("Em665_IL1b")),
    }

    if il1b_measurement:
        for key, value in il1b_values.items():
            setattr(il1b_measurement, key, value)
        return il1b_measurement

    if any(value is not None for value in il1b_values.values()):
        il1b_measurement = Il1b(
            well_id=well.id,
            type="imaged_based",
            image_type="il1b",
            IL1bPosCells_count=0.0,
            Il1bCircularity=0.0,
            Il1bDiameter=0.0,
            IL1bCompactness=0.0,
            Il1bAnisometry=0.0,
            IL1bTotalIntensity_CH3=0.0,
            **il1b_values,
        )
        session.add(il1b_measurement)
        session.flush()
        return il1b_measurement

    return None


def _import_tnfa(session: Session, well, row: dict):
    tnfa_measurement = (
        session.query(Tnfa)
        .filter(Tnfa.well_id == well.id)
        .first()
    )

    tnfa_values = {
        "Em616": _to_float(row.get("Em616_TNFa")),
        "Em665": _to_float(row.get("Em665_TNFa")),
        "Count": _to_float(row.get("[Cell_SpeckTNFaCells] (TNFa (cells)) COUNT (AVG)")),
        "Area_Total": _to_float(row.get("[Cell_SpeckTNFaCells] (TNFa (cells)) Area TOTAL (AVG)")),
        "Area_Avg": _to_float(row.get("[Cell_SpeckTNFaCells] (TNFa (cells)) Area AVG (AVG)")),
        "Diameter_Total": _to_float(row.get("[Cell_SpeckTNFaCells] (TNFa (cells)) Diameter TOTAL (AVG)")),
        "Diameter_Avg": _to_float(row.get("[Cell_SpeckTNFaCells] (TNFa (cells)) Diameter AVG (AVG)")),
    }

    if tnfa_measurement:
        for key, value in tnfa_values.items():
            setattr(tnfa_measurement, key, value)
        return tnfa_measurement

    if any(value is not None for value in tnfa_values.values()):
        tnfa_measurement = Tnfa(
            well_id=well.id,
            type="imaged_based",
            image_type="tnfa",
            **tnfa_values,
        )
        session.add(tnfa_measurement)
        session.flush()
        return tnfa_measurement

    return None


def import_measurement(session: Session, row: dict):
    well = row.get("__well")
    if well is None:
        raise ValueError("import_measurement requires row['__well'] with a Well instance")

    il1b_measurement = _import_il1b(session, well, row)
    tnfa_measurement = _import_tnfa(session, well, row)

    return il1b_measurement or tnfa_measurement


def get_or_create_default_measurement(session: Session, well, row=None):
    if row is not None:
        row_dict = row.to_dict() if hasattr(row, "to_dict") else dict(row)
        row_dict["__well"] = well
        measurement = import_measurement(session, row_dict)
        if measurement is not None:
            return measurement

        return session.query(Measurement).filter_by(well_id=well.id).first()

    measurement = session.query(Measurement).filter_by(
        type="measurement",
        well_id=well.id).first()
    if not measurement:
        measurement = Measurement(
            type="measurement",
            well_id=well.id
        )
        session.add(measurement)
        session.flush()
    return measurement