from sqlalchemy import Column, Integer, String, Float, Interval, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.orderinglist import ordering_list
from database import Base

class Substance(Base):
    __tablename__ = 'substances'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    catalog_id = Column(String, nullable=False)
    vendor = Column(String, nullable=False)
    lot = Column(String, nullable=False)
    treatments = relationship("Treatment", back_populates="substance")

class ConditionClass(Base):
    __tablename__ = 'conditionclasses'
    id = Column(Integer, primary_key=True)
    name = Column(String(30), nullable=False)
    description = Column(String, nullable=False)
    conditions = relationship("Condition", back_populates="conditionclass")

class Condition(Base):
    __tablename__ = 'conditions'
    id = Column(Integer, primary_key=True)
    conditionclass_id = Column(Integer, ForeignKey('conditionclasses.id'), nullable=False)
    conditionclass = relationship("ConditionClass", back_populates="conditions")
    treatments = relationship("Treatment", order_by="Treatment.position",
                              collection_class=ordering_list('position'),
                              back_populates="condition")
    experiments = relationship("Experiment", back_populates="condition")

class Treatment(Base):
    __tablename__ = 'treatments'
    id = Column(Integer, primary_key=True)
    type = Column(String(25), nullable=False)
    substance_id = Column(Integer, ForeignKey('substances.id'), nullable=False)
    concentration = Column(Float, nullable=False)
    concentration_unit = Column(String(10), nullable=False)
    duration = Column(Interval, nullable=False)
    condition_id = Column(Integer, ForeignKey('conditions.id'), nullable=False)
    position = Column(Integer, nullable=False)
    substance = relationship("Substance", back_populates="treatments")
    condition = relationship("Condition", back_populates="treatments")

class Experiment(Base):
    __tablename__ = 'experiments'
    id = Column(Integer, primary_key=True)
    well_id = Column(Integer, ForeignKey('wells.id'), nullable=False)
    measurement_id = Column(Integer, ForeignKey('measurements.id'), nullable=False)
    condition_id = Column(Integer, ForeignKey('conditions.id'))
    qc = Column(String(4), nullable=False, default='pass')
    well = relationship("Well", back_populates="experiments")
    measurement = relationship("Measurement", back_populates="experiments")
    condition = relationship("Condition", back_populates="experiments")