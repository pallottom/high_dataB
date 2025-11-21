from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Measurement(Base):
    __tablename__ = 'measurements'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    instrument_name = Column(String, nullable=False)
    settings = Column(JSON, nullable=True)
    #experiments = relationship("Experiment", back_populates="measurement", uselist=False)

    well_id = Column(Integer, ForeignKey('wells.id'), nullable=False)
    well = relationship("Well", back_populates="measurements")

     # --- Fluorescence intensities ---
    em616_il1b = Column(Float)
    em616_tnfa = Column(Float)
    em665_il1b = Column(Float)
    em665_tnfa = Column(Float)

    # --- Ratios ---
    delta_ratio_il1b = Column(Float)
    delta_ratio_tnfa = Column(Float)

    # --- Interpolation QC flags ---
    check_interpol_il1b = Column(Boolean)
    check_interpol_tnfa = Column(Boolean)

    # --- Cell counts & IL-1β metrics ---
    cells_count = Column(Integer)
    il1b_poscells_count = Column(Integer)
    il1b_poscells_percent = Column(Float)
    il1b_rel_pgml = Column(Float)

    # --- Nuclear morphology ---
    nuc_count = Column(Integer)
    nuc_circularity = Column(Float)
    nuc_mean_area_um2 = Column(Float)
    nuc_mean_intensity = Column(Float)

    # --- Speck formation metrics ---
    speck_count = Column(Integer)
    speckposcells_count = Column(Integer)
    speckposcells_percent = Column(Float)
    speckposcells_multispeck_count = Column(Integer)
    speckposcells_multispeck_percent = Column(Float)

    # --- TNFα positive cell metrics ---
    tnfa_poscells_count = Column(Integer)
    tnfa_poscells_percent = Column(Float)
    tnfa_rel_pgml = Column(Float)

    def __repr__(self):
        return f"<Measurement id={self.id}, well_id={self.well_id}, name={self.name}>"