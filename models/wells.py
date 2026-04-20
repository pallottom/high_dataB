"""
Module: wells.py

Purpose:
    Defines the Well model representing a physical location (coordinate) within a plate.
    Each well holds exactly one specimen and can have associated measurements (HTRF, image-based, etc.).
    
Cardinality:
    - Many wells belong to one plate.
    - Each well holds exactly one specimen (many wells can hold the same specimen in different plates).
    - Each well has at most one Experiment state record (one-to-one relationship).
    - Each well can have many Measurement records (one-to-many).

Key Design Decisions:
    - well_key is the canonical coordinate (e.g., A01, B12) — row and column are derived from this, not stored.
    - plate_id is non-null because every well must belong to a plate.
    - specimen_id is non-null because a well must always hold a specimen.
    - experiment_id is an optional one-to-one link to experiments.id.
    - UniqueConstraint(plate_id, well_key) prevents duplicate well coordinates within the same plate.
    - Indexes on plate_id and specimen_id optimize FK lookups for high-throughput queries.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base



class Well(Base):
    """
    Represents a physical well location within a plate in a high-throughput assay.
    
    Attributes:
        id (int): Primary key.
        well_key (str): Canonical well coordinate, e.g., 'A01', 'B12', 'H08'.
                       Format is derived from (row, column) but not stored separately to avoid redundancy.
        specimen_id (int): Foreign key to specimens table. Non-null; every well must hold a specimen.
        plate_id (int): Foreign key to plates table. Non-null; every well must belong to a plate.
        experiment_id (int): Optional foreign key to experiments.id.
    
    Relationships:
        plate: Many-to-one. This well belongs to exactly one plate.
        specimen: Many-to-one. This well holds exactly one specimen.
        experiment: One-to-one (uselist=False). This well has at most one Experiment state record.
        measurements: One-to-many. This well can have multiple measurements (Tnfa, Il1b, Nuc, etc.).
    
    Constraints:
        - UniqueConstraint(plate_id, well_key): No duplicate well_key within the same plate.
        - Both specimen_id and plate_id are non-null.
        - Indexes on plate_id and specimen_id for performance optimization in large datasets.
    """

    __tablename__ = 'wells'
    
    # Table-level constraints:
    # - UniqueConstraint: Composite unique on (plate_id, well_key) prevents duplicate well coordinates per plate.
    # - Indexes: Optimize foreign key lookups on plate_id and specimen_id for rapid queries in high-throughput workflows.
    __table_args__ = (
        UniqueConstraint('plate_id', 'well_key', name='uq_plate_well_key'),
        Index('idx_well_plate_id', 'plate_id'),
        Index('idx_well_specimen_id', 'specimen_id'),
    )
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Canonical well coordinate (e.g., A01, B12, H08).
    # Row/column are NOT stored separately; they are derived from well_key to avoid redundancy.
    well_key = Column(String(3), nullable=False)
    
    # Foreign key to specimens table. Non-null: every well must hold exactly one specimen.
    # index=True redundantly set (already indexed via __table_args__ Indexes), but explicit for clarity.
    specimen_id = Column(Integer, ForeignKey("specimens.id"), nullable=False, index=True)

    # Foreign key to plates table. Non-null: every well must belong to exactly one plate.
    # This is the table context that gives the well its meaning within a screening run.
    plate_id = Column(Integer, ForeignKey('plates.id'), nullable=False)

    # Optional one-to-one link to experiment state.
    experiment_id = Column(Integer, ForeignKey('experiments.id'), unique=True)

    # Relationships
    # ============
    
    # Many-to-one: This well belongs to exactly one plate.
    # Plate.wells provides the reverse (one plate has many wells).
    plate = relationship("Plate", back_populates="wells")
    
    # Many-to-one: This well holds exactly one specimen.
    # Specimen.wells provides the reverse (one specimen appears in many wells across different plates).
    specimen = relationship("Specimen", back_populates="wells")
    
    # One-to-one: This well has at most one Experiment state record (uselist=False enforces singular).
    # Experiment.well provides the reverse. Useful for storing QC pass/fail status per well.
    experiment = relationship("Experiment", back_populates="well", uselist=False, foreign_keys=[experiment_id])
    
    # One-to-many: This well can have multiple numeric measurement values.
    # MeasurementValue.well provides the reverse.
    measurements = relationship("MeasurementValue", back_populates="well")
    
    # experiment_id is stored directly on the well as the one-to-one experiment link.
