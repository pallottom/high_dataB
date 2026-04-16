import pandas as pd
from sqlalchemy.orm import Session

from models import (
    MeasurementValue,
    Essay,
    IMMUNX,
    SequencingExperiment,
    PrimaryFeature,
)


def _to_float(value):
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _get_or_create_feature(session: Session, key: str, name: str, unit: str | None = None):
    feature = session.query(PrimaryFeature).filter_by(key=key).first()
    if feature:
        return feature
    feature = PrimaryFeature(key=key, name=name, unit=unit)
    session.add(feature)
    session.flush()
    return feature


def _get_or_create_experiment(session: Session, exp_type: str):
    exp = session.query(Essay).filter_by(type=exp_type).first()
    if exp:
        return exp

    cls_map = {
        "immunx": IMMUNX,
        "homogeneous": IMMUNX,
        "image_based": Essay,
        "sequencing": SequencingExperiment,
    }
    exp_cls = cls_map.get(exp_type, Essay)
    exp = exp_cls(type=exp_type)
    session.add(exp)
    session.flush()
    return exp


def _collect_measurements(row: dict):
    # Map source columns to canonical primary-feature keys.
    mappings = [
        ("em616", "Em616_TNFa", "Em616 signal", None),
        ("em665", "Em665_TNFa", "Em665 signal", None),
        ("em616", "Em616_IL1b", "Em616 signal", None),
        ("em665", "Em665_IL1b", "Em665 signal", None),
        ("count", "[Cell_SpeckTNFaCells] (TNFa (cells)) COUNT (AVG)", "Cell count", "cells"),
        ("area", "[Cell_SpeckTNFaCells] (TNFa (cells)) Area AVG (AVG)", "Area", None),
        ("area_total", "[Cell_SpeckTNFaCells] (TNFa (cells)) Area TOTAL (AVG)", "Area total", None),
        ("diameter", "[Cell_SpeckTNFaCells] (TNFa (cells)) Diameter AVG (AVG)", "Diameter", None),
        ("diameter_total", "[Cell_SpeckTNFaCells] (TNFa (cells)) Diameter TOTAL (AVG)", "Diameter total", None),
    ]

    collected = []
    for key, source_col, name, unit in mappings:
        value = _to_float(row.get(source_col))
        if value is not None:
            collected.append((key, name, unit, value))
    return collected


def import_measurement(session: Session, row: dict):
    well = row.get("__well")
    if well is None:
        raise ValueError("import_measurement requires row['__well'] with a Well instance")

    exp_type = "image_based"
    experiment = _get_or_create_experiment(session, exp_type)

    values = _collect_measurements(row)
    created = []
    for feature_key, feature_name, feature_unit, numeric_value in values:
        feature = _get_or_create_feature(session, feature_key, feature_name, feature_unit)
        measurement = MeasurementValue(
            value=numeric_value,
            experiment_id=experiment.id,
            primary_feature_id=feature.id,
            well_id=well.id,
            replicate_index=0,
        )
        session.add(measurement)
        created.append(measurement)

    if created:
        session.flush()
        return created[0]
    return None


def get_or_create_default_measurement(session: Session, well, row=None):
    if row is not None:
        row_dict = row.to_dict() if hasattr(row, "to_dict") else dict(row)
        row_dict["__well"] = well
        measurement = import_measurement(session, row_dict)
        if measurement is not None:
            return measurement

    return (
        session.query(MeasurementValue)
        .filter_by(well_id=well.id)
        .order_by(MeasurementValue.id.asc())
        .first()
    )
