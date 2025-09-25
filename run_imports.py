import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import *
from importers import import_management, import_specimen, import_measurement, import_wells, import_experiment

engine = create_engine("postgresql+psycopg2://postgres:postgres@localhost:5432/test_marta_2", echo=True)
Session = sessionmaker(bind=engine)

def run_import(csv_file):
    df = pd.read_csv(csv_file)
    session = Session()

    default_measurement = import_measurement.get_or_create_default_measurement(session)

    for _, row in df.iterrows():
        donor_id = row["donor_ID"]
        experiment_barcode = row["barcode_exp"]
        plate_barcode = row["plate"]
        well_key = row["wellname"]

        # Management
        project = import_management.import_project(session, "Group name to be added")
        screen = import_management.import_screen(session, project, experiment_barcode, experiment_barcode, "Experiment description")
        plate = import_management.import_plate(session, screen, row["plate"], plate_barcode, row["date_exp"])

        # Specimen
        human_donor = import_specimen.import_specimen(session, donor_id, row)

        # Well
        well = import_wells.import_well(session, plate, human_donor, well_key, row="1", col="2")

        # Experiments
        import_experiment.import_experiment(session, row, well, default_measurement)

    session.commit()
    session.close()

if __name__ == "__main__":
    run_import("../test_DB/data/IMXPR04_postATP_ready4FeatureVector_JB_20220224 (copy).csv")
    print("✅ Data loading completed")