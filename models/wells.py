from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base





class Well(Base):
    __tablename__ = 'wells'
    id = Column(Integer, primary_key=True)
    well_key = Column(String(3), nullable=False)
    row = Column(Integer, nullable=False)
    col = Column(Integer, nullable=False)
    specimen_id = Column(Integer, ForeignKey("specimens.id"), nullable=False)

    #experiment_id = Column(Integer, ForeignKey('experiments.id'))

    plate_id = Column(Integer, ForeignKey('plates.id'))
    specimen_id = Column(Integer, ForeignKey('specimens.id'))


    plate = relationship("Plate", back_populates="wells")
    experiments = relationship("Experiment", back_populates="wells")
    specimen = relationship("Specimen", back_populates="well") 
    measurements = relationship("Measurement", back_populates="wells")


    #def __repr__(self):
     #   return f"<Well(id={self.id}, well_name='{self.id}')>"