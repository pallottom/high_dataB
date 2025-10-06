from sqlalchemy import Integer, String, Float, Column, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


"""from sqlalchemy import Enum
SpecimenTypeEnum = Enum("cell", "bacteria", "virus", "unknown", name="specimen_type")
type = Column(SpecimenTypeEnum, nullable=False)
"""




class Specimen(Base):
    __tablename__ = "specimens"
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String, nullable=False)  # example: "cell", "bacteria", "virus"

    wells = relationship("Well", back_populates="specimen")
    # Might need to add barcode# 

    __mapper_args__ = {
        'polymorphic_identity': 'specimen',
        'polymorphic_on': type
    }

    def __repr__(self):
        # Generic representation that works for all specimen types
        return f"<Specimen(id={self.id}, type={self.type})>"


class CellSpecimen(Specimen):
    __tablename__ = "cell_specimens"  # Consistent naming
    id = Column(Integer, ForeignKey("specimens.id"), primary_key=True)
    name = Column(String, unique=True)  # e.g., "PBMC", "Liver", "Neuron", "Unknown"

    __mapper_args__ = {
        'polymorphic_identity': 'cell',
    }

    def __repr__(self):
        return f"<CellSpecimen(id={self.id}, name={self.name})>"


class BacteriaSpecimen(Specimen):
    __tablename__ = "bacteria_specimens"
    id = Column(Integer, ForeignKey("specimens.id"), primary_key=True)
    species = Column(String)

    __mapper_args__ = {
        "polymorphic_identity": "bacteria"
    }

    def __repr__(self):
        return f"<BacteriaSpecimen(id={self.id}, species={self.species})>"


class VirusSpecimen(Specimen):
    __tablename__ = "virus_specimens"
    id = Column(Integer, ForeignKey("specimens.id"), primary_key=True)
    species = Column(String)

    __mapper_args__ = {
        "polymorphic_identity": "virus"
    }

    def __repr__(self):
        return f"<VirusSpecimen(id={self.id}, species={self.species})>"


class DonorType(Specimen):
    __tablename__ = "donor_types"
    id = Column(Integer, ForeignKey("specimens.id"), primary_key=True)
    donor_category = Column(String, nullable=False)  # "human", "mouse", etc.

    # Relationship to CellSpecimen (a donor type can have multiple cell specimens)
    cell_type_id = Column(Integer, ForeignKey("cell_specimens.id"), nullable=False)
    cell_type = relationship("CellSpecimen", back_populates="donor_types")
    
    __mapper_args__ = {
        'polymorphic_identity': 'donor' # it was donor_type
    }

class HumanDonor(DonorType):
    __tablename__ = "human_donors"
    id = Column(Integer, ForeignKey("donor_types.id"), primary_key=True)
    name = Column(String)
    age = Column(Integer)
    gender = Column(String)
    # Other human-specific fields
    
    __mapper_args__ = {
        "polymorphic_identity": "human"
    }

class MouseDonor(DonorType):
    __tablename__ = "mouse_donors"
    id = Column(Integer, ForeignKey("donor_types.id"), primary_key=True)
    strain = Column(String)
    age_weeks = Column(Integer)
    # Other mouse-specific fields
    
    __mapper_args__ = {
        "polymorphic_identity": "mouse"
    }








