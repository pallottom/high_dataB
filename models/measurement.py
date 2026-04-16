"""
Module: measurement.py

Purpose:
        Defines the measurement branch of the assay database, including the
        measurement experiment hierarchy (Essay, IMMUNX, SequencingExperiment),
        feature dictionary, and numeric measurement facts.

Model overview:
        - Essay: Polymorphic base table for measurement experiment types.
        - IMMUNX: Specialized experiment subtype with target/population/
            biological component metadata.
        - Target, Population, CellCompartment: Lookup tables used by IMMUNX.
        - PrimaryFeature: Canonical dictionary of measurable feature keys.
        - MeasurementValue: Fact table storing numeric values per
            well/experiment/feature combination.

Cardinality:
        - One Essay experiment can have many MeasurementValue rows.
        - One Well can have many MeasurementValue rows.
        - One PrimaryFeature can be referenced by many MeasurementValue rows.
        - One IMMUNX row can reference one Target, one Population,
            and one CellCompartment.

Key Design Decisions:
        - Joined-table inheritance is used for experiment subtypes.
        - Feature definitions are normalized in a dedicated dictionary table.
        - Measurement identity is protected by a composite unique constraint on
            (well_id, experiment_id, primary_feature_id, replicate_index).
"""

from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from database import Base


class Essay(Base):
    """
    Base class for measurement experiment types.
    Child tables: immunx, image_based, sequencing.
    This gives freedom to add experiment-specific metadata in the future while keeping a common interface for measurements.
    """

    __tablename__ = "Essay"

    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)  # immunx, image_based, sequencing

    measurements = relationship("MeasurementValue", back_populates="experiment")

    __mapper_args__ = {
        "polymorphic_identity": "measurement_experiment",
        "polymorphic_on": type,
    }
class Target(Base):
    __tablename__ = "target"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1024), nullable=True)

    immunx_experiments = relationship("IMMUNX", back_populates="target")


class Population(Base):
    __tablename__ = "population"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1024), nullable=True)

    immunx_experiments = relationship("IMMUNX", back_populates="population")


class CellCompartment(Base):
    __tablename__ = "cell_compartment"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1024), nullable=True)

    immunx_experiments = relationship("IMMUNX", back_populates="biological_component")


class IMMUNX(Essay):
    __tablename__ = "immunx"

    id = Column(Integer, ForeignKey("Essay.id"), primary_key=True)
    target_id = Column(Integer, ForeignKey("target.id"), nullable=True)
    population_id = Column(Integer, ForeignKey("population.id"), nullable=True)
    biological_component_id = Column(Integer, ForeignKey("cell_compartment.id"), nullable=True)

    target = relationship("Target", back_populates="immunx_experiments")
    population = relationship("Population", back_populates="immunx_experiments")
    biological_component = relationship("CellCompartment", back_populates="immunx_experiments")

    __mapper_args__ = {
        "polymorphic_identity": "immunx",
    }



class SequencingExperiment(Essay):
    __tablename__ = "sequencing"

    id = Column(Integer, ForeignKey("Essay.id"), primary_key=True)

    __mapper_args__ = {
        "polymorphic_identity": "sequencing",
    }


class PrimaryFeature(Base):
    """
    Canonical measurement feature dictionary.
    Examples: area, volume, diameter, number.
    """

    __tablename__ = "feature"

    __table_args__ = (
        UniqueConstraint("key", name="uq_primary_feature_key"),
    )

    id = Column(Integer, primary_key=True)
    key = Column(String(100), nullable=False)
    name = Column(String(255), nullable=False)
    unit = Column(String(50), nullable=True)

    measurements = relationship("MeasurementValue", back_populates="primary_feature")


class MeasurementValue(Base):
    """
    Single fact table for numeric measurements.
    """

    __tablename__ = "measurement_values"

    __table_args__ = (
        UniqueConstraint(
            "well_id",
            "experiment_id",
            "primary_feature_id",
            "replicate_index",
            name="uq_measurement_value_identity",
        ),
        Index("idx_measurement_value_feature_experiment", "primary_feature_id", "experiment_id"),
        Index("idx_measurement_value_well", "well_id"),
        Index("idx_measurement_value_experiment", "experiment_id"),
    )

    id = Column(Integer, primary_key=True)
    value = Column(Float, nullable=False)

    experiment_id = Column(Integer, ForeignKey("Essay.id"), nullable=False)
    primary_feature_id = Column(Integer, ForeignKey("feature.id"), nullable=False)
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=False)

    replicate_index = Column(Integer, nullable=False, default=0)

    experiment = relationship("Essay", back_populates="measurements")
    primary_feature = relationship("PrimaryFeature", back_populates="measurements")
    well = relationship("Well", back_populates="measurements")

