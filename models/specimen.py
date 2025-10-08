from sqlalchemy import Integer, String, Column, ForeignKey, Sequence
from sqlalchemy.orm import relationship
from database import Base

# Shared sequence for unique IDs across all specimen types
specimen_id_seq = Sequence('specimen_id_seq', start=1)

class Specimen(Base):
    __tablename__ = "specimens"  # Must be a real table for inheritance
    id = Column(Integer, specimen_id_seq, primary_key=True, server_default=specimen_id_seq.next_value())
    type = Column(String(50), nullable=False)  # "human", "mouse", "virus", "bacteria"


    well = relationship("Well", back_populates="specimen")
    
    
    __mapper_args__ = {
        'polymorphic_identity': 'specimen',
        'polymorphic_on': type
    }

    def __repr__(self):
        return f"<Specimen(id={self.id}, type='{self.type}')>"


class HumanDonor(Specimen):
    __tablename__ = "human_donor"
    id = Column(Integer, ForeignKey("specimens.id"), primary_key=True)

    human_name = Column(String(100), nullable=False)
    cell_type_id = Column(Integer, ForeignKey("cell_type.id"), nullable=False)
    cell_characteristic_id = Column(Integer, ForeignKey("cell_characteristics.id"), nullable=False)
    age = Column(Integer)
    sex = Column(String(1))

    # Relationships
    cell_type = relationship("CellType")
    cell_characteristic = relationship("CellCharacteristics")

    __mapper_args__ = {
        'polymorphic_identity': 'human',
    }


class MouseDonor(Specimen):
    __tablename__ = "mouse_donor"
    id = Column(Integer, ForeignKey("specimens.id"), primary_key=True)

    name = Column(String(100), nullable=False)
    cell_type_id = Column(Integer, ForeignKey("cell_type.id"), nullable=False)
    cell_characteristic_id = Column(Integer, ForeignKey("cell_characteristics.id"), nullable=False)
    strain = Column(String(50))
    transgene = Column(String(50))

    # Relationships
    cell_type = relationship("CellType")
    cell_characteristic = relationship("CellCharacteristics")
    #wells = relationship("Well", back_populates="specimen")

    __mapper_args__ = {
        'polymorphic_identity': 'mouse',
    }


class Virus(Specimen):
    __tablename__ = "virus"
    id = Column(Integer, ForeignKey("specimens.id"), primary_key=True)
    virus_name = Column(String(100), nullable=False)
    virus_type = Column(String(50))  # "DNA", "RNA"

    __mapper_args__ = {
        'polymorphic_identity': 'virus'
    }


class Bacteria(Specimen):
    __tablename__ = "bacteria"
    id = Column(Integer, ForeignKey("specimens.id"), primary_key=True)
    bacteria_name = Column(String(100), nullable=False)
    bacteria_type = Column(String(50))  # "gram+", "gram-"

    __mapper_args__ = {
        'polymorphic_identity': 'bacteria'
    }


class CellType(Base):
    __tablename__ = "cell_type"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cell_type_name = Column(String(50), nullable=False, unique=True)  # "PBMC", "liver", "neurons"


class CellCharacteristics(Base):  # fixed spelling
    __tablename__ = "cell_characteristics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    characteristic_name = Column(String(100), nullable=False, unique=True)  # "CD4+", "CD8+", etc.
