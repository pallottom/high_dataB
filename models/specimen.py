from sqlalchemy import Integer, String, Float, Column, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class SpecimenType(Base):
    __tablename__ = "specimen_types"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)  # "cell", "bacteria", "virus"

    donors = relationship("Donor", back_populates="specimen_type")

    def __repr__(self):
        return f"<SpecimenType(id={self.id}, name={self.name})>"

class DonorType(Base):
    __tablename__ = "donor_types"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)  # "human", "mouse"

    cell_types = relationship("CellType", back_populates="donor_type")

    def __repr__(self):
        return f"<DonorType(id={self.id}, name={self.name})>"

class CellType(Base):
    __tablename__ = "cell_types"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)  # "PBMC", "liver", etc.

    specimen_type_id = Column(Integer, ForeignKey("specimen_types.id"))
    donor_type_id = Column(Integer, ForeignKey("donor_types.id"))

    specimen_type = relationship("SpecimenType")
    donor_type = relationship("DonorType", back_populates="cell_types")
    human_donors = relationship("HumanDonor", back_populates="cell_type")

    def __repr__(self):
        return f"<CellType(id={self.id}, name={self.name})>"

# --- Polymorphic donor hierarchy ---

class Donor(Base):
    __tablename__ = 'donors'
    id = Column(Integer, primary_key=True)
    type = Column(String(50))  # 'human', 'bacteria', 'virus'

    specimen_type_id = Column(Integer, ForeignKey("specimen_types.id"))
    specimen_type = relationship("SpecimenType", back_populates="donors")

    # 1-to-1 with Well
    well = relationship("Well", back_populates="donor")

    __mapper_args__ = {
        'polymorphic_identity': 'donor',
        'polymorphic_on': type
    }

    def __repr__(self):
        return f"<Donor(id={self.id}, type={self.type})>"

class HumanDonor(Donor):
    __tablename__ = 'human_donors'
    id = Column(Integer, ForeignKey('donors.id'), primary_key=True)

    # Donor metadata
    name = Column(String, nullable=False)
    sex = Column(String)
    age = Column(Integer)
    weight_kg = Column(Float)
    height_cm = Column(Float)
    bmi = Column(Float)
    smoker = Column(String)
    ethnicity = Column(String)
    donor_loc = Column(String)
    age_group = Column(String)
    class_bmi = Column(String)
    class_weight = Column(String)
    donor_class = Column(String)  

    # Link to CellType, which connects further to DonorType + SpecimenType
    cell_type_id = Column(Integer, ForeignKey("cell_types.id"))
    cell_type = relationship("CellType", back_populates="human_donors")

    __mapper_args__ = {
        'polymorphic_identity': 'human'
    }

    def __repr__(self):
        return f"<HumanDonor(id={self.id}, name={self.name}, cell_type={self.cell_type.name if self.cell_type else None})>"

class BacteriaDonor(Donor):
    __tablename__ = 'bacteria_donors'
    id = Column(Integer, ForeignKey('donors.id'), primary_key=True)
    bacteria_type_id = Column(Integer, ForeignKey("bacteria_types.id"))

    bacteria_type = relationship("BacteriaType")

    __mapper_args__ = {
        'polymorphic_identity': 'bacteria'
    }

class VirusDonor(Donor):
    __tablename__ = 'virus_donors'
    id = Column(Integer, ForeignKey('donors.id'), primary_key=True)
    virus_type_id = Column(Integer, ForeignKey("virus_types.id"))

    virus_type = relationship("VirusType")

    __mapper_args__ = {
        'polymorphic_identity': 'virus'
    }

# --- Concrete types for bacteria/virus ---
class BacteriaType(Base):
    __tablename__ = "bacteria_types"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    specimen_type_id = Column(Integer, ForeignKey("specimen_types.id"))
    specimen_type = relationship("SpecimenType")

class VirusType(Base):
    __tablename__ = "virus_types"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    specimen_type_id = Column(Integer, ForeignKey("specimen_types.id"))
    specimen_type = relationship("SpecimenType")