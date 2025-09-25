from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Well(Base):
    __tablename__ = 'wells'
    id = Column(Integer, primary_key=True)
    well_key = Column(String, nullable=False)
    col = Column(String)
    row = Column(String)
    plate_id = Column(Integer, ForeignKey('plates.id'))
    donor_id = Column(Integer, ForeignKey('donors.id'), nullable=False)
    plate = relationship("Plate", back_populates="wells")
    donor = relationship("Donor", back_populates="well")
    experiments = relationship("Experiment", back_populates="well")