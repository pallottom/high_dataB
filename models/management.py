from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    group_name = Column(String, unique=True)
    screens = relationship("Screen", back_populates="project")

class Screen(Base):
    __tablename__ = 'screens'
    id = Column(Integer, primary_key=True)
    screen_name = Column(String, nullable=False, unique=True)
    screen_description = Column(String)
    barcode = Column(String)
    project_id = Column(Integer, ForeignKey('projects.id'))
    project = relationship("Project", back_populates="screens")
    plates = relationship("Plate", back_populates="screen")

class Plate(Base):
    __tablename__ = 'plates'
    id = Column(Integer, primary_key=True)
    plate_name = Column(String, nullable=False)
    barcode = Column(String)
    date_experiment = Column(String)
    screen_id = Column(Integer, ForeignKey('screens.id'))
    screen = relationship("Screen", back_populates="plates")
    wells = relationship("Well", back_populates="plate")
    locations = relationship("Location", back_populates="plate")

class Location(Base):
    __tablename__ = 'locations'
    id = Column(Integer, primary_key=True)
    path = Column(String, nullable=False)
    barcode_id = Column(Integer, ForeignKey('plates.id'))
    plate = relationship("Plate", back_populates="locations")