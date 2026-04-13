"""
Module: management.py

Purpose:
    Defines the management and organizational models for the assay database:
    Project, Screen, Plate, and Location.
    These models capture the hierarchy from project-level organization down to
    individual experimental plates and their associated file-system locations.

Cardinality:
    - One project can have many screens.
    - One project can have many plates.
    - One screen belongs to one project and can contain many plates.
    - One plate can have many wells and many location records.
    - One location belongs to one plate.

Key Design Decisions:
    - Project stores both a human-readable name and a unique group_name used by imports.
    - Screen numbers are unique only within a project, enforced by a composite unique constraint.
    - Plate links both to its screen and directly to its project for easier querying and import logic.
    - Location stores filesystem metadata related to a plate, such as image and source paths.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


class Project(Base):
    """
    Represents a top-level project grouping for screening data.

    Attributes:
        id (int): Primary key.
        name (str): Human-readable project name. Unique when provided.
        group_name (str): Unique grouping key used to identify the project during imports.

    Relationships:
        screens: One-to-many. A project can contain many screens.
        plates: One-to-many. A project can contain many plates.

    Constraints:
        - name is unique.
        - group_name is unique.
    """

    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    group_name = Column(String, unique=True)

    screens = relationship("Screen", back_populates="project")
    plates = relationship("Plate", back_populates="project")

class Screen(Base):
    """
    Represents a screen within a project.

    Attributes:
        id (int): Primary key.
        screen_number (int): Screen identifier unique within a project.
        screen_description (str): Optional descriptive text for the screen.
        barcode (str): Optional barcode associated with the screen.
        project_id (int): Foreign key to the owning project.

    Relationships:
        project: Many-to-one. Each screen belongs to exactly one project.
        plates: One-to-many. A screen can contain many plates.

    Constraints:
        - UniqueConstraint(screen_number, project_id): The same screen number may
          appear in different projects, but not twice within the same project.
    """

    __tablename__ = 'screens'
    __table_args__ = (UniqueConstraint('screen_number', 'project_id', name='uq_screen_number_project'),)
    id = Column(Integer, primary_key=True)
    screen_number = Column(Integer, nullable=False)
    screen_description = Column(String)
    barcode = Column(String)
    project_id = Column(Integer, ForeignKey('projects.id'))

    # Relationships
    # ============

    project = relationship("Project", back_populates="screens")
    plates = relationship("Plate", back_populates="screen", foreign_keys="Plate.screen_id")


class Plate(Base):
    """
    Represents an experimental plate within a screen and project.

    Attributes:
        id (int): Primary key.
        name (str): Plate name. Required.
        barcode (str): Optional plate barcode.
        date_experiment (str): Experiment date associated with the plate.
        screen_id (int): Foreign key to the parent screen.
        project_id (int): Foreign key to the parent project.

    Relationships:
        screen: Many-to-one. Each plate belongs to one screen.
        project: Many-to-one. Each plate belongs to one project.
        wells: One-to-many. A plate contains many wells.
        locations: One-to-many. A plate can have many location/file references.
    """

    __tablename__ = 'plates'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    barcode = Column(String)
    date_experiment = Column(String)
    screen_id = Column(Integer, ForeignKey('screens.id'))
    project_id = Column(Integer, ForeignKey('projects.id'))

    # Relationships
    # ============

    # Many-to-one: Each plate belongs to one screen.
    screen = relationship("Screen", back_populates="plates")
    wells = relationship("Well", back_populates="plate")
    locations = relationship("Location", back_populates="plate")
    project = relationship("Project", back_populates="plates")


class Location(Base):
    """
    Represents filesystem location metadata associated with a plate.

    Attributes:
        id (int): Primary key.
        img_path (str): Required image path associated with a plate.
        source_path (str): Optional source file path used during ingestion.
        barcode_id (int): Foreign key to the related plate.

    Relationships:
        plate: Many-to-one. Each location record belongs to one plate.
    """

    __tablename__ = 'locations'
    id = Column(Integer, primary_key=True)
    img_path = Column(String, nullable=False)
    source_path = Column(String)
    barcode_id = Column(Integer, ForeignKey('plates.id'))

    plate = relationship("Plate", back_populates="locations")