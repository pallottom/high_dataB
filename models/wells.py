from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base





class Well(Base):
    __tablename__ = 'wells'
    id = Column(Integer, primary_key=True)
    well_key = Column(String(3), nullable=False)
    row = Column(Integer, nullable=False)
    col = Column(Integer, nullable=False)
    plate_id = Column(Integer, ForeignKey('plates.id'))
    donor_id = Column(Integer, ForeignKey('donors.id'))
    plate = relationship("Plate", back_populates="wells")
    donor = relationship("Donor", back_populates="well")
    experiments = relationship("Experiment", back_populates="well")