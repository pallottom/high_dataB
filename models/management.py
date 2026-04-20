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
    - Plate.barcode is the physical-plate identifier and must be unique.
    - Plate barcode format is validated as: <ACRONYM>PR##S##R##p## (e.g., IMXPR01S04R01p06).
    - Plate links both to its screen and directly to its project for easier querying and import logic.
    - Location stores filesystem metadata related to a plate, such as image and source paths.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, CheckConstraint
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
        project_id (int): Foreign key to the owning project.

    Relationships:
        project: Many-to-one. Each screen belongs to exactly one project.
        plates: One-to-many. A screen can contain many plates.
        imagings: One-to-many. A screen can contain multiple imaging setups.

    Constraints:
        - UniqueConstraint(screen_number, project_id): The same screen number may
          appear in different projects, but not twice within the same project.
    """

    __tablename__ = 'screens'
    __table_args__ = (UniqueConstraint('screen_number', 'project_id', name='uq_screen_number_project'),)
    id = Column(Integer, primary_key=True)
    screen_number = Column(Integer, nullable=False)
    screen_description = Column(String)
    project_id = Column(Integer, ForeignKey('projects.id'))

    # Relationships
    # ============

    project = relationship("Project", back_populates="screens")
    plates = relationship("Plate", back_populates="screen", foreign_keys="Plate.screen_id")
    imagings = relationship("Imaging", back_populates="screen")


class Imaging(Base):
    """
    Imaging setup associated with a screen.

    Attributes:
        id (int): Primary key.
        screen_id (int): Foreign key to the related screen.
        instrument (str): Instrument used for acquisition.

    Relationships:
        screen: Many-to-one. Parent screen for this imaging setup.
        channels: One-to-many. Channels configured for this imaging setup.
    """

    __tablename__ = 'imaging'

    id = Column(Integer, primary_key=True)
    screen_id = Column(Integer, ForeignKey('screens.id'), nullable=False)
    instrument = Column(String, nullable=False)

    screen = relationship("Screen", back_populates="imagings")
    channels = relationship("Channel", back_populates="imaging")


class Antibody(Base):
    """
    Antibody reference used by imaging channels.

    Attributes:
        id (int): Primary key.
        vendor (str): Antibody vendor.
        lot (str): Lot identifier.
        catalogue_number (str): Vendor catalogue number.
        coniugated_fluorochrome (str): Conjugated fluorochrome label.

    Relationships:
        channels: One-to-many. Channels that use this antibody.
    """

    __tablename__ = 'antibodies'

    id = Column(Integer, primary_key=True)
    vendor = Column(String, nullable=False)
    lot = Column(String, nullable=True)
    catalogue_number = Column(String, nullable=True)
    coniugated_fluorochrome = Column(String, nullable=True)

    channels = relationship("Channel", back_populates="antibody")


class Channel(Base):
    """
    Channel metadata for one imaging setup.

    Attributes:
        id (int): Primary key.
        imaging_id (int): Foreign key to the parent imaging setup.
        channel_number (int): Ordered channel index (e.g., 1..N).
        filter_set (str): Filter set used for the channel.
        antibody_id (int): Optional foreign key to antibodies.id.
        staining_target (str): Biological target for staining.

    Relationships:
        imaging: Many-to-one. Parent imaging setup.
        antibody: Many-to-one. Optional antibody used for the channel.
    """

    __tablename__ = 'channels'
    __table_args__ = (
        UniqueConstraint('imaging_id', 'channel_number', name='uq_channel_per_imaging'),
    )

    id = Column(Integer, primary_key=True)
    imaging_id = Column(Integer, ForeignKey('imaging.id'), nullable=False)
    channel_number = Column(Integer, nullable=False)
    filter_set = Column(String, nullable=True)
    antibody_id = Column(Integer, ForeignKey('antibodies.id'), nullable=True)
    staining_target = Column(String, nullable=True)

    imaging = relationship("Imaging", back_populates="channels")
    antibody = relationship("Antibody", back_populates="channels")


class Plate(Base):
    """
    Represents an experimental plate within a screen and project.

    Attributes:
        id (int): Primary key.
        name (str): Plate name. Required.
        barcode (str): Required unique plate barcode (physical-plate identifier).
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
    __table_args__ = (
        UniqueConstraint('barcode', name='uq_plate_barcode'),
        CheckConstraint(
            "barcode ~ '^[A-Z]{3}PR[0-9]{2}S[0-9]{2}R[0-9]{2}p[0-9]{2}$'",
            name='ck_plate_barcode_format',
        ),
    )

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    barcode = Column(String, nullable=False)
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