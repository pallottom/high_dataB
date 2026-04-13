"""
Module: experiment.py

Purpose:
    Defines the experiment branch of the assay database, including substances,
    condition grouping, ordered treatments, and per-well experiment state.

Model overview:
    - Substance: Chemical metadata for compounds used in treatments.
    - ConditionClass: Named grouping of related conditions.
    - Condition: Ordered sequence of treatments linked to one condition class.
    - Treatment: One application step in a condition (compound, dose, unit, duration, order).
    - Experiment: The experiment state attached to one well, optionally linked to a condition.

Cardinality:
    - One Substance can be used in many Treatments.
    - One ConditionClass contains many Conditions.
    - One Condition contains many Treatments (ordered by position).
    - One Condition can be referenced by many Experiments.
    - One Well has at most one Experiment (enforced by unique well_id).

Key Design Decisions:
    - Treatments are ordered using ordering_list on Treatment.position.
    - Treatment has a composite unique constraint to avoid duplicate treatment steps in a condition.
    - concentration_unit is restricted with a check constraint.
    - Experiment uses a one-to-one link with Well via unique well_id.

Note: Code adapted from screendb repo
"""

from sqlalchemy import Column, Integer, String, Float, Interval, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.orderinglist import ordering_list
from database import Base

class Substance(Base):
    """
    Chemical reference table used by treatments.

    Attributes:
        id (int): Primary key.
        hash (str): Compound hash identifier. Unique and required.
        name (str): Substance name.
        type (str): Substance category/type.
        catalog_id (str): Vendor catalog identifier.
        vendor (str): Vendor name.
        lot (str): Lot identifier.

    Relationships:
        treatments: One-to-many. One substance can be used in many treatments.

    Original note:
        Substance contains chemical information about a substance that can be
        used in Treatments.
    """
    __tablename__ = 'substances'
    id = Column(Integer, primary_key=True)
    hash = Column(String(64), unique=True, nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    catalog_id = Column(String, nullable=False)
    vendor = Column(String, nullable=False)
    lot = Column(String, nullable=False)
    treatments = relationship("Treatment", back_populates="substance")

class ConditionClass(Base):
    """
    Named grouping of related conditions.

    Attributes:
        id (int): Primary key.
        name (str): Condition class name.
        description (str): Human-readable description.

    Relationships:
        conditions: One-to-many. A condition class contains many conditions.

    Notes:
        Used to query and organize experiments by shared condition family labels.

    Original note:
        A collection of conditions.
        Main reason for this type is to enable to query well experiments by
        conditionclass names, e.g. 'sample_prim01_activ01'.
    """
    __tablename__ = 'conditionclasses'
    id = Column(Integer, primary_key=True)
    name = Column(String(30), nullable=False)
    description = Column(String, nullable=False)
    conditions = relationship("Condition", back_populates="conditionclass")

class Condition(Base):
    """
    Ordered sequence of treatments belonging to one condition class.

    Attributes:
        id (int): Primary key.
        conditionclass_id (int): Foreign key to conditionclasses.id.

    Relationships:
        conditionclass: Many-to-one. Parent condition class.
        treatments: One-to-many. Ordered treatment steps for this condition.
        experiments: One-to-many. Experiments that reference this condition.

    Notes:
        Treatment ordering is controlled by Treatment.position and ordering_list.

    Original note:
        A Condition is an ordered sequence of treatments.
        The order of treatments is defined in ConditionTreatmentCross.
        The Condition table assigns each Condition to a Conditionclass.
    """
    __tablename__ = 'conditions'
    id = Column(Integer, primary_key=True)
    conditionclass_id = Column(Integer, ForeignKey('conditionclasses.id'), nullable=False)
    conditionclass = relationship("ConditionClass", back_populates="conditions")
    treatments = relationship("Treatment", order_by="Treatment.position",
                              collection_class=ordering_list('position'),
                              back_populates="condition")
    experiments = relationship("Experiment", back_populates="condition")

class Treatment(Base):
    """
    One treatment step inside a condition.

    Attributes:
        id (int): Primary key.
        type (str): Treatment type/category.
        substance_id (int): Foreign key to substances.id.
        concentration (float): Concentration value.
        concentration_unit (str): Concentration unit (validated by check constraint).
        duration (Interval): Incubation duration.
        condition_id (int): Foreign key to conditions.id.
        position (int): Order of this treatment within its condition.

    Relationships:
        substance: Many-to-one. Substance used in this treatment.
        condition: Many-to-one. Condition this treatment belongs to.

    Constraints:
        - Composite unique constraint on (type, substance_id, concentration,
          concentration_unit, duration, condition_id, position).
        - Check constraint restricting concentration_unit to allowed values.

    Original note:
        A Treatment is an element of a Condition (the Condition is an ordered
        sequence of treatments).
        It contains information which substance is applied, at which concentration
        and how long it was incubated.

        Treatment.position specifies the order within the associated Condition.
        The position is automatically set when Treatment is initialized
        as follows:

        >>t1 = Treatment(..)
        >>t2 = Treatment(..)
        >>cond = Condition()
        >>cond.ordered_treatments.append(t1) # position=0
        >>cond.ordered_treatments.append(t2) # position=1
    """
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
    """
    Experiment state associated with one well.

    Attributes:
        id (int): Primary key.
        well_id (int): Foreign key to wells.id. Unique and required.
        condition_id (int): Optional foreign key to conditions.id.
        qc (str): Quality-control status (default 'pass').

    Relationships:
        well: One-to-one. Each well has at most one experiment.
        condition: Many-to-one. Optional assigned condition.

    Notes:
        The unique constraint on well_id enforces one experiment record per well.

    Original note:
        An Experiment is a certain state of a Well. An Experiment includes
        a Well, a Condition (a sequence of Treatments) of that well
        and a Measurement. Experiments will be associated with experiment_results
        in the future.
    """
    __tablename__ = 'experiments'
    id = Column(Integer, primary_key=True)
    well_id = Column(Integer, ForeignKey('wells.id'), unique=True, nullable=False)
    #measurement_id = Column(Integer, ForeignKey('measurements.id'), nullable=False)
    condition_id = Column(Integer, ForeignKey('conditions.id'))
    qc = Column(String(4), nullable=False, default='pass')
    well = relationship("Well", back_populates="experiment", uselist=False)
    #measurement = relationship("Measurement", back_populates="experiments")
    condition = relationship("Condition", back_populates="experiments")