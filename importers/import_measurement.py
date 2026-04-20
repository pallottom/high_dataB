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
    mapping_path = Path(__file__).resolve().parent.parent / "config" / "column_mapping.csv"

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

    return rows


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
    target = session.query(Target).filter_by(name=name).first()
    if target:
        return target
    target = Target(name=name)
    session.add(target)
    session.flush()
    return target


def _get_or_create_population(session: Session, name: str | None):
    if not name:
        return None
    population = session.query(Population).filter_by(name=name).first()
    if population:
        return population
    population = Population(name=name)
    session.add(population)
    session.flush()
    return population


def _get_or_create_cell_compartment(session: Session, name: str | None):
    if not name:
        return None
    compartment = session.query(CellCompartment).filter_by(name=name).first()
    if compartment:
        return compartment
    compartment = CellCompartment(name=name)
    session.add(compartment)
    session.flush()
    return compartment


def _get_or_create_primary_feature(
    session: Session,
    source_column: str,
    feature_name: str | None,
    unit: str | None,
):
    key = source_column
    name = feature_name or source_column

    feature = session.query(PrimaryFeature).filter_by(key=key).first()
    if feature:
        if feature_name and feature.name != name:
            feature.name = name
        if unit and feature.unit != unit:
            feature.unit = unit
        return feature

    feature = PrimaryFeature(key=key, name=name, unit=unit)
    session.add(feature)
    session.flush()
    return feature


def _get_or_create_immunx_experiment(
    session: Session,
    target_id: int | None,
    population_id: int | None,
    cell_compartment_id: int | None,
    emission: float | None,
):
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
    return experiment


def import_measurement(session: Session, row: dict):
    """
    Import measurements from one row using config/column_mapping.csv.
    Default essay type is IMMUNX.

    Required input:
    - row['__well'] with a Well ORM instance.
    """
    well = row.get("__well")
    if well is None:
        raise ValueError("import_measurement requires row['__well'] with a Well instance")

    mapping_rows = _load_column_mapping()
    created_or_updated = []

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

        measurement = (
            session.query(MeasurementValue)
            .filter_by(
                well_id=well.id,
                essay_id=experiment.id,
                feature_id=feature.id,
                replicate_index=0,
            )
            .first()
        )

        if measurement is None:
            measurement = MeasurementValue(
                value=numeric_value,
                essay_id=experiment.id,
                feature_id=feature.id,
                well_id=well.id,
                replicate_index=0,
            )
            session.add(measurement)
        else:
            measurement.value = numeric_value

        created_or_updated.append(measurement)

    if created_or_updated:
        session.flush()
        return created_or_updated[0]
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
