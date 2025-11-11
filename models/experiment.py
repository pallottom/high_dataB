from sqlalchemy import Column, Integer, String, Float, Interval, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.orderinglist import ordering_list
from database import Base

class Substance(Base):
    '''
    Substance contains chemical information about a substance that can be
    used in Treatments.
    '''
    __tablename__ = 'substances'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    catalog_id = Column(String, nullable=False)
    vendor = Column(String, nullable=False)
    lot = Column(String, nullable=False)
    treatments = relationship("Treatment", back_populates="substance")

class ConditionClass(Base):
    '''
    A collection of conditions.
    Main reason for this type is to enable to query well experiments by
    conditionclass names, e.g. 'sample_prim01_activ01'
    '''
    __tablename__ = 'conditionclasses'
    id = Column(Integer, primary_key=True)
    name = Column(String(30), nullable=False)
    description = Column(String, nullable=False)
    conditions = relationship("Condition", back_populates="conditionclass")

class Condition(Base):
    '''
    A Condition is an ordered sequence of treatments.
    The order of treatments is defined in ConditionTreatmentCross.
    The Condition table assigns each Condition to a Conditionclass.
    '''
    __tablename__ = 'conditions'
    id = Column(Integer, primary_key=True)
    conditionclass_id = Column(Integer, ForeignKey('conditionclasses.id'), nullable=False)
    conditionclass = relationship("ConditionClass", back_populates="conditions")
    treatments = relationship("Treatment", order_by="Treatment.position",
                              collection_class=ordering_list('position'),
                              back_populates="condition")
    experiments = relationship("Experiment", back_populates="condition")

class Treatment(Base):
    '''
    A Treatment is an element of a Condition (the Condition is an ordered
    sequence of treatments).
    It contains information which substance is applied, at which concentration
    and how long it was incubated.

    Treatment.position specifies the order within the associcated Condition.
    The position is automatically set when Treatment is initialized
    as follows:

    >>t1 = Treatment(..)
    >>t2 = Treatment(..)
    >>cond = Condition()
    >>cond.ordered_treatments.append(t1) # position=0
    >>cond.ordered_treatments.append(t2) # position=1
    '''
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
    
    units_allowed = "'mM', 'uM', 'nM', 'ugml', 'mgml', 'ngml'"

    __table_args__ = (
        UniqueConstraint(type,
                    substance_id,
                    concentration,
                    concentration_unit,
                    duration,
                    condition_id,
                    position)
        ,
        CheckConstraint(
            "(concentration_unit in ({}))".format(units_allowed),
            name='concentrationunitcheck'))
    


class Experiment(Base):
    '''
    An Experiment is a certain state of a Well. An Experiment includes
    a Well, a Condition (a sequence of Treatments) of that well
    and a Measurement. Experiments will be associated with experiment_results
    in the future.
    '''
    __tablename__ = 'experiments'
    id = Column(Integer, primary_key=True)
    well_id = Column(Integer, ForeignKey('wells.id'), unique=True, nullable=False)
    #measurement_id = Column(Integer, ForeignKey('measurements.id'), nullable=False)
    condition_id = Column(Integer, ForeignKey('conditions.id'))
    qc = Column(String(4), nullable=False, default='pass')
    wells = relationship("Well", back_populates="experiments", uselist=False) # uselist is a 1-1 constraint
    #measurement = relationship("Measurement", back_populates="experiments")
    condition = relationship("Condition", back_populates="experiments")