from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    group_name = Column(String, unique=True)

    screens = relationship("Screen", back_populates="project")
    plates = relationship("Plate", back_populates="project")

class Screen(Base):
    __tablename__ = 'screens'
    __table_args__ = (UniqueConstraint('screen_number', 'project_id', name='uq_screen_number_project'),)
    id = Column(Integer, primary_key=True)
    screen_number = Column(Integer, nullable=False)
    screen_description = Column(String)
    barcode = Column(String)
    project_id = Column(Integer, ForeignKey('projects.id'))
    #plate_id = Column(Integer, ForeignKey('plates.id'))

    project = relationship("Project", back_populates="screens")
    plates = relationship("Plate", back_populates="screen", foreign_keys="Plate.screen_id")

class Plate(Base):
    __tablename__ = 'plates'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    barcode = Column(String)
    date_experiment = Column(String)
    screen_id = Column(Integer, ForeignKey('screens.id'))
    project_id = Column(Integer, ForeignKey('projects.id'))

    screen = relationship("Screen", back_populates="plates")
    wells = relationship("Well", back_populates="plate")
    locations = relationship("Location", back_populates="plate")
    project = relationship("Project", back_populates="plates")

class Location(Base):
    __tablename__ = 'locations'
    id = Column(Integer, primary_key=True)
    img_path = Column(String, nullable=False)
    source_path = Column(String)
    barcode_id = Column(Integer, ForeignKey('plates.id'))

    plate = relationship("Plate", back_populates="locations")