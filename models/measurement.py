from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, ForeignKey, Sequence
from sqlalchemy.orm import relationship
from database import Base

measurement_id_seq = Sequence('specimen_id_seq', start=1)


#### PARENT CLASS #####

class Measurement(Base):
    __tablename__="measurement"
    id = Column(Integer, measurement_id_seq, primary_key=True, server_default=measurement_id_seq.next_value())
    type = Column(String(50), nullable=False)  # "homogeneous", "image_based", "sequencing"
    well_id = Column(Integer, ForeignKey("wells.id"), nullable=False) 

    well = relationship("Well", back_populates="measurements")


    
    __mapper_args__ = {
        'polymorphic_identity': 'measurement',
        'polymorphic_on': type  # quello che passa alla child class
    }

    def __repr__(self):
        return f"<Measurement(id={self.id}, type='{self.type}')>"
    


#### MEASUREMENT CHILD CLASSES #####

class Homogeneous(Measurement):
    __tablename__ = "homogeneous"
    id = Column(Integer, ForeignKey("measurement.id"), primary_key=True)

    homogeneous_type = Column(String(100), nullable=False)

    # Relationships

    __mapper_args__ = {
        'polymorphic_identity': 'homogeneous',
        'polymorphic_on': homogeneous_type 
    }


class ImageBased(Measurement):
    __tablename__ = "image_based"
    id = Column(Integer, ForeignKey("measurement.id"), primary_key=True)

    image_type = Column(String(100), nullable=False)

    # Relationships

    __mapper_args__ = {
        'polymorphic_identity': 'imaged_based',
        'polymorphic_on': image_type 
    }


#### HOMOGENEOUS CHILD CLASSES #####

class Hhf(Homogeneous):
    __tablename__ = "hhf"
    id = Column(Integer, ForeignKey("homogeneous.id"), primary_key=True)

    em616_IL1b = Column(Float, nullable=False)
    em665_IL1b = Column(Float, nullable=False)

    # Relationships

    __mapper_args__ = {
        'polymorphic_identity': 'hhf',
    }


class Enzymatic(Homogeneous):
    __tablename__ = "enzymatic"
    id = Column(Integer, ForeignKey("homogeneous.id"), primary_key=True)

    col1 = Column(Float, nullable=False)
    col2 = Column(Float, nullable=False)

    # Relationships

    __mapper_args__ = {
        'polymorphic_identity': 'enzymatic',
    }


#### IMAGE_BASED CHILD CLASSES #####

class Nuc(ImageBased):
    __tablename__ = "Nuc"
    id = Column(Integer, ForeignKey("image_based.id"), primary_key=True)

    Cells_count = Column(Float, nullable=False)
    Area = Column(Float, nullable=False)
    Diameter = Column(Float, nullable=False)

    # Relationships

    __mapper_args__ = {
        'polymorphic_identity': 'nuc',
    }

class Tnfa(ImageBased):
    __tablename__ = "tnfa"
    id = Column(Integer, ForeignKey("image_based.id"), primary_key=True)

    TNFaPosCells_count= Column(Float, nullable=False)
    TNFaPosCells_AreaCOUNT = Column(Float, nullable=False)
    TNFaPosCells_AreaTOT = Column(Float, nullable=False)
    TNFaPosCells_AVG = Column(Float, nullable=False)

    # Relationships

    __mapper_args__ = {
        'polymorphic_identity': 'tnfa',
    }

class Il1b(ImageBased):
    __tablename__ = "il1b"
    id = Column(Integer, ForeignKey("image_based.id"), primary_key=True)

    IL1bPosCells_count= Column(Float, nullable=False)
    Il1bCircularity = Column(Float, nullable=False)
    Il1bDiameter = Column(Float, nullable=False)
    IL1bCompactness = Column(Float, nullable=False)
    Il1bAnisometry = Column(Float, nullable=False)
    IL1bTotalIntensity_CH3 = Column(Float, nullable=False)

    # Relationships

    __mapper_args__ = {
        'polymorphic_identity': 'il1b',
    }
