from models import ConditionClass, Condition, Substance, Treatment, Experiment
import pandas as pd


def import_condition_class(session, name, description=None):
    """Get or create a ConditionClass by name."""
    cc = session.query(ConditionClass).filter_by(name=name).first()
    if not cc:
        cc = ConditionClass(
            name=name,
            description=description or f"Condition class for {name}"
        )
        session.add(cc)
        session.flush()
    return cc


def import_condition(session, condition_class):
    """Get or create a Condition for a given ConditionClass."""
    condition = session.query(Condition).filter_by(conditionclass_id=condition_class.id).first()
    if not condition:
        condition = Condition(conditionclass=condition_class)
        session.add(condition)
        session.flush()
    return condition


def import_substance(session, name, type="small_molecule", vendor="default_vendor"):
    """Get or create a Substance by name."""
    if not name or not pd.notna(name):
        return None

    substance = session.query(Substance).filter_by(name=str(name)).first()
    if not substance:
        substance = Substance(
            name=str(name),
            type=type,
            catalog_id=f"CAT_{name}",
            vendor=vendor,
            lot=f"LOT_{name}"
        )
        session.add(substance)
        session.flush()
    return substance


def import_treatment(session, condition, position, treatment_type,
                     substance, concentration=0, concentration_unit="nM", duration_min=0):
    if not substance:
        return None

    duration_str = f"{duration_min} minutes"  ## Option to add datetime# 

    existing = session.query(Treatment).filter(  # was filter_by
        Treatment.type == treatment_type,
        Treatment.substance_id == substance.id,
        Treatment.concentration == concentration,
        Treatment.concentration_unit == concentration_unit,
        Treatment.duration == duration_str,
        Treatment.condition_id == condition.id,  # Changed from 'condition' to 'condition_id'
        Treatment.position == position
    ).first()

    if existing:
        return existing

    treatment = Treatment(
        type=treatment_type,
        substance_id=substance.id,
        concentration=concentration,
        concentration_unit=concentration_unit,
        duration=duration_str,
        condition_id=condition.id,
        position=position
    )
    session.add(treatment)
    return treatment


def import_experiment(session, row, well, measurement):
    """
    Orchestrates ConditionClass, Condition, Substances, Treatments, Experiment creation.
    row = pandas row with input data.
    """
    # --- ConditionClass ---
    condition_class_name = row.get("condition_class", "default_condition_class")
    condition_class = import_condition_class(session, condition_class_name)

    # --- Condition ---
    condition = import_condition(session, condition_class)

    # --- Substances ---
    prim_substance = import_substance(session, row.get("prim_name"))
    activ_substance = import_substance(session, row.get("activ_name"))

    # --- Treatments ---
    if prim_substance:
        import_treatment(
            session,
            condition,
            position=0,
            treatment_type="primary",
            substance=prim_substance,
            concentration=row.get("prim_conc", 0),
            concentration_unit=row.get("prim_conc_unit", "nM"),
            duration_min=row.get("prim_time_min", 0),
        )

    if activ_substance:
        import_treatment(
            session,
            condition,
            position=1,
            treatment_type="activator",
            substance=activ_substance,
            concentration=row.get("activ_conc", 0),
            concentration_unit=row.get("activ_conc_unit", "nM"),
            duration_min=row.get("activ_time_min", 0),
        )

    # --- Experiment ---
    experiment = session.query(Experiment).filter_by(
        well_id=well.id, 
        condition_id=condition.id
        ).first()
    
    if not experiment:
        htrf_data_il1b = row.get("htrf_il1b_data")
        htrf_data_tnfa = row.get("htrf_tnfa_data")
        qc_status = "pass" if (pd.notna(htrf_data_il1b) or pd.notna(htrf_data_tnfa)) else "fail"

        experiment = Experiment(
            well_id=well.id,
            condition_id=condition.id,
            #measurement_id=measurement.id,
            qc=qc_status
        )
        session.add(experiment)
    return experiment
