import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import *
from importers import import_management, import_specimen, import_measurement, import_wells, import_experiment
import re
from database import SessionLocal



def _parse_barcode(barcode):
    """
    Parse barcode with format: IMXPR04S05R01p01
    - Prefix: IMX (or any letters before PR)
    - Project number: follows PR
    - Screen number: follows S
    - Run number: follows R
    - Plate number: follows p (lowercase)
    
    Example: IMXPR04S05R01p01 -> ('IMX', 4, 5, 1, 1)
    """
    # Pattern explanation:
    # ^([A-Z]+) - prefix: one or more uppercase letters at start
    # PR(\d+) - project number: digits after PR
    # S(\d+) - screen number: digits after S
    # R(\d+) - run number: digits after R
    # p(\d+)$ - plate number: digits after lowercase p at end
    
    pattern = r'^([A-Z]+)PR(\d+)S(\d+)R(\d+)p(\d+)$'
    
    match = re.match(pattern, barcode)
    
    if not match:
        raise ValueError(
            f"Invalid barcode format: '{barcode}'. "
            f"Expected format: <PREFIX>PR<NUM>S<NUM>R<NUM>p<NUM> (e.g., IMXPR04S05R01p01)"
        )
    
    prefix, project_num, screen_number, run_num, plate_num = match.groups()
    
    return (
        prefix,
        str(project_num),
        str(screen_number),
        str(run_num),
        str(plate_num)
    )



def run_import(csv_file):
    df = pd.read_csv(csv_file)
    session = SessionLocal()

    default_measurement = import_measurement.get_or_create_default_measurement(session)

    for _, row in df.head(150).iterrows():
        donor_id = row["donor_ID"]
        experiment_barcode = row["barcode"]
        plate_barcode = row["barcode"]
        well_key = row["wellname"]
        date_exp = row.get("date_exp", "unknown_date")
        #project_num= _parse_barcode(experiment_barcode)


        prefix, project_num, screen_number, run_num, plate_num = _parse_barcode(experiment_barcode)


        # Management
        project = import_management.import_project(session, "Group name to be added")
        screen = import_management.import_screen(session, project, screen_number, experiment_barcode, "Experiment description")
        plate = import_management.import_plate(session, screen, plate_num, plate_barcode, date_exp, project)

        # Specimen
        human_donor = import_specimen.import_specimen(session, row)

        # Well

        well = import_wells.import_well(session, plate, well_key, human_donor, screen=screen)

        # Experiments
        import_experiment.import_experiment(session, row, well, default_measurement)

    session.commit()
    session.close()

if __name__ == "__main__":
    run_import("../test_DB/data/IMXPR05S07R04R05_wi_htrf_icc_20250917_JB.csv")

    print("✅ Data loading completed")



    """ "C:/Users/pallottom/Documents/Projects/screendb/screendb/test_data/metadata_import/IMXPR04S02_E01_wellinfo_20201202.csv" """


    """ ../test_DB/data/IMXPR04_postATP_ready4FeatureVector_JB_20220224 (copy).csv """



"""../test_DB/data/IMXPR03S14R02R05_wi_htrf_asc_20251003_JB(in).csv""" # Mouse data

"""../test_DB/data/GVS_20250822_extendedfeatures.csv""" # New Human data 
"""../test_DB/data/IMXPR05S07R04R05_wi_htrf_icc_20250917_JB.csv""" # New Human data 