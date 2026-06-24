from pathlib import Path
import csv

import pandas as pd
from sqlalchemy.orm import Session

from models import (
    CellCompartment,
    IMMUNX,
    MeasurementValue,
    Population,
    PrimaryFeature,
    Target,
)


_COLUMN_MAPPING_CACHE = None


def _get_measurement_cache(session: Session):
    cache = session.info.get("measurement_cache")
    if cache is not None:
        return cache

    targets_by_name = {obj.name: obj for obj in session.query(Target).all()}
    populations_by_name = {obj.name: obj for obj in session.query(Population).all()}
    compartments_by_name = {obj.name: obj for obj in session.query(CellCompartment).all()}
    features_by_key = {obj.key: obj for obj in session.query(PrimaryFeature).all()}

    immunx_by_identity = {}
    for obj in session.query(IMMUNX).all():
        key = (obj.target_id, obj.population_id, obj.cell_compartment_id, obj.emission)
        immunx_by_identity[key] = obj

    cache = {
        "targets_by_name": targets_by_name,
        "populations_by_name": populations_by_name,
        "compartments_by_name": compartments_by_name,
        "features_by_key": features_by_key,
        "immunx_by_identity": immunx_by_identity,
    }
    session.info["measurement_cache"] = cache
    return cache


def _normalize_text(value):
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text if text else None


def _to_float(value):
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _load_column_mapping():
    global _COLUMN_MAPPING_CACHE
    if _COLUMN_MAPPING_CACHE is not None:
        return _COLUMN_MAPPING_CACHE

    mapping_path = Path(__file__).resolve().parent.parent / "column_mapping.csv"

    with mapping_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        headers = next(reader, None)

        if not headers:
            return []

        headers = [str(h).strip() for h in headers]
        expected_len = len(headers)
        mapping_records = []

        for raw_row in reader:
            if not raw_row or all(not str(cell).strip() for cell in raw_row):
                continue

            # Be tolerant to malformed rows (e.g., extra trailing commas in mapping CSV).
            if len(raw_row) < expected_len:
                normalized_row = raw_row + [""] * (expected_len - len(raw_row))
            elif len(raw_row) > expected_len:
                normalized_row = raw_row[:expected_len]
            else:
                normalized_row = raw_row

            mapping_records.append(dict(zip(headers, normalized_row)))

    rows = []
    for mapping_row in mapping_records:
        source_column = _normalize_text(mapping_row.get("source_column"))
        if not source_column:
            continue

        rows.append(
            {
                "source_column": source_column,
                "feature_name": _normalize_text(mapping_row.get("feature_name")),
                "unit": _normalize_text(mapping_row.get("unit")),
                # Support both naming variants to be robust against mapping edits.
                "target_name": _normalize_text(mapping_row.get("target_name") or mapping_row.get("target")),
                "population_name": _normalize_text(mapping_row.get("population_name")),
                "cell_compartment_name": _normalize_text(
                    mapping_row.get("cell_compartment_name") or mapping_row.get("cell-compartment_name")
                ),
                "emission": _to_float(mapping_row.get("emission")),
            }
        )

    _COLUMN_MAPPING_CACHE = rows
    return _COLUMN_MAPPING_CACHE


def _lookup_row_value(row: dict, source_column: str):
    if source_column in row:
        return row.get(source_column)

    source_lc = source_column.strip().lower()
    for key, value in row.items():
        if str(key).strip().lower() == source_lc:
            return value
    return None


def _get_or_create_target(session: Session, name: str | None):
    if not name:
        return None
    cache = _get_measurement_cache(session)
    target = cache["targets_by_name"].get(name)
    if target is None:
        target = session.query(Target).filter_by(name=name).first()
    if target:
        cache["targets_by_name"][name] = target
        return target
    target = Target(name=name)
    session.add(target)
    session.flush()
    cache["targets_by_name"][name] = target
    return target


def _get_or_create_population(session: Session, name: str | None):
    if not name:
        return None
    cache = _get_measurement_cache(session)
    population = cache["populations_by_name"].get(name)
    if population is None:
        population = session.query(Population).filter_by(name=name).first()
    if population:
        cache["populations_by_name"][name] = population
        return population
    population = Population(name=name)
    session.add(population)
    session.flush()
    cache["populations_by_name"][name] = population
    return population


def _get_or_create_cell_compartment(session: Session, name: str | None):
    if not name:
        return None
    cache = _get_measurement_cache(session)
    compartment = cache["compartments_by_name"].get(name)
    if compartment is None:
        compartment = session.query(CellCompartment).filter_by(name=name).first()
    if compartment:
        cache["compartments_by_name"][name] = compartment
        return compartment
    compartment = CellCompartment(name=name)
    session.add(compartment)
    session.flush()
    cache["compartments_by_name"][name] = compartment
    return compartment


def _get_or_create_primary_feature(
    session: Session,
    source_column: str,
    feature_name: str | None,
    unit: str | None,
):
    key = source_column
    name = feature_name or source_column

    cache = _get_measurement_cache(session)
    feature = cache["features_by_key"].get(key)
    if feature is None:
        feature = session.query(PrimaryFeature).filter_by(key=key).first()

    if feature:
        if feature_name and feature.name != name:
            feature.name = name
        if unit and feature.unit != unit:
            feature.unit = unit
        cache["features_by_key"][key] = feature
        return feature

    feature = PrimaryFeature(key=key, name=name, unit=unit)
    session.add(feature)
    session.flush()
    cache["features_by_key"][key] = feature
    return feature


def _get_or_create_immunx_experiment(
    session: Session,
    target_id: int | None,
    population_id: int | None,
    cell_compartment_id: int | None,
    emission: float | None,
):
    cache = _get_measurement_cache(session)
    key = (target_id, population_id, cell_compartment_id, emission)
    experiment = cache["immunx_by_identity"].get(key)
    if experiment is None:
        experiment = (
            session.query(IMMUNX)
            .filter_by(
                target_id=target_id,
                population_id=population_id,
                cell_compartment_id=cell_compartment_id,
                emission=emission,
            )
            .first()
        )

    if experiment:
        cache["immunx_by_identity"][key] = experiment
        return experiment

    experiment = IMMUNX(
        type="immunx",
        emission=emission,
        target_id=target_id,
        population_id=population_id,
        cell_compartment_id=cell_compartment_id,
    )
    session.add(experiment)
    session.flush()
    cache["immunx_by_identity"][key] = experiment
    return experiment


def import_measurement(session: Session, row: dict):
    """
    Import measurements from one row using column_mapping.csv in the repo root.
    Default essay type is IMMUNX.

    Required input:
    - row['__well'] with a Well ORM instance.
    """
    well = row.get("__well")
    if well is None:
        raise ValueError("import_measurement requires row['__well'] with a Well instance")

    mapping_rows = _load_column_mapping()
    resolved_rows = []
    essay_ids = set()
    feature_ids = set()

    for mapping in mapping_rows:
        source_column = mapping["source_column"]
        numeric_value = _to_float(_lookup_row_value(row, source_column))
        if numeric_value is None:
            continue

        target = _get_or_create_target(session, mapping["target_name"])
        population = _get_or_create_population(session, mapping["population_name"])
        compartment = _get_or_create_cell_compartment(session, mapping["cell_compartment_name"])

        experiment = _get_or_create_immunx_experiment(
            session,
            target_id=target.id if target else None,
            population_id=population.id if population else None,
            cell_compartment_id=compartment.id if compartment else None,
            emission=mapping["emission"],
        )

        feature = _get_or_create_primary_feature(
            session,
            source_column=source_column,
            feature_name=mapping["feature_name"],
            unit=mapping["unit"],
        )

        essay_ids.add(experiment.id)
        feature_ids.add(feature.id)
        resolved_rows.append(
            {
                "well_id": well.id,
                "essay_id": experiment.id,
                "feature_id": feature.id,
                "replicate_index": 0,
                "value": numeric_value,
            }
        )

    if not resolved_rows:
        return None

    existing_rows = (
        session.query(
            MeasurementValue.id,
            MeasurementValue.well_id,
            MeasurementValue.essay_id,
            MeasurementValue.feature_id,
            MeasurementValue.replicate_index,
        )
        .filter(
            MeasurementValue.well_id == well.id,
            MeasurementValue.replicate_index == 0,
            MeasurementValue.essay_id.in_(essay_ids),
            MeasurementValue.feature_id.in_(feature_ids),
        )
        .all()
    )

    existing_by_identity = {
        (m.well_id, m.essay_id, m.feature_id, m.replicate_index): m.id
        for m in existing_rows
    }

    insert_mappings = []
    update_mappings = []
    for row_mapping in resolved_rows:
        identity = (
            row_mapping["well_id"],
            row_mapping["essay_id"],
            row_mapping["feature_id"],
            row_mapping["replicate_index"],
        )
        existing_id = existing_by_identity.get(identity)

        if existing_id is None:
            insert_mappings.append(row_mapping)
        else:
            update_mappings.append(
                {
                    "id": existing_id,
                    "value": row_mapping["value"],
                }
            )

    if insert_mappings:
        session.bulk_insert_mappings(MeasurementValue, insert_mappings)

    if update_mappings:
        session.bulk_update_mappings(MeasurementValue, update_mappings)

    session.flush()
    return (
        session.query(MeasurementValue)
        .filter_by(well_id=well.id)
        .order_by(MeasurementValue.id.asc())
        .first()
    )


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
