import pandas as pd
from importers import import_management, import_specimen, import_measurement, import_wells, import_experiment
import re
from database import SessionLocal
import os



def _parse_barcode(barcode):
    """
    Parse barcode with format: IMXPR04S05R01p01
    - Prefix: 3 uppercase letters (project acronym), e.g. IMX
    - Project number: PR + 2 digits
    - Sprint/screen number: S + 2 digits
    - Run number: R + 2 digits
    - Plate number: p + 2 digits (lowercase p)
    
    Example: IMXPR04S05R01p01 -> ('IMX', 4, 5, 1, 1)
    """
    # Pattern explanation:
    # ^([A-Z]{3}) - prefix: exactly 3 uppercase letters at start
    # PR(\d{2}) - project number: 2 digits after PR
    # S(\d{2}) - sprint/screen number: 2 digits after S
    # R(\d{2}) - run number: 2 digits after R
    # p(\d{2})$ - plate number: 2 digits after lowercase p at end
    
    pattern = r'^([A-Z]{3})PR(\d{2})S(\d{2})R(\d{2})p(\d{2})$'
    
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


def _row_get(row_dict, *candidates, default=None, required=False):
    """Return the first non-empty value found for candidate column names."""
    for candidate in candidates:
        if candidate in row_dict and pd.notna(row_dict[candidate]):
            return row_dict[candidate]

    lowered = {str(k).strip().lower(): v for k, v in row_dict.items()}
    for candidate in candidates:
        value = lowered.get(str(candidate).strip().lower())
        if pd.notna(value):
            return value

    if required:
        raise ValueError(f"Missing required column(s): {', '.join(candidates)}")
    return default



def run_import(
    csv_file,
    img_path=None,
    source_path=None,
    specimen_type=None,
    group_name=None,
    project_name=None,
    screen_description=None,
    max_rows_per_file=None,
):
    df = pd.read_csv(csv_file)
    if max_rows_per_file is not None:
        df = df.head(int(max_rows_per_file))

    session = SessionLocal()

    for _, row in df.iterrows(): #df.head(150).iterrows():  #df.iterrows()
        row = row.copy()
        row_dict = row.to_dict()

        if specimen_type is not None:
            row["specimen"] = specimen_type
            row_dict["specimen"] = specimen_type

        experiment_barcode = _row_get(row_dict, "barcode", "Barcode", required=True)
        plate_barcode = experiment_barcode
        well_key = _row_get(row_dict, "wellname", "well_name", "well", required=True)
        date_exp = _row_get(row_dict, "date_exp", "date", default="unknown_date")


        prefix, project_num, screen_number, run_num, plate_num = _parse_barcode(experiment_barcode)


        # Management
        project = import_management.import_project(session, group_name or "Group name to be added", project_name)
        screen = import_management.import_screen(session, project, screen_number, screen_description)
        plate = import_management.import_plate(session, screen, plate_num, plate_barcode, date_exp, project)
        import_management.import_location(session, plate, img_path, source_path)

        # Specimen
        specimen = import_specimen.import_specimen(session, row_dict)

        # Well
        well = import_wells.import_well(session, plate, well_key, specimen, screen=screen)

        # Measurement branch (now linked to well)
        measurement_row = dict(row_dict)
        measurement_row["__well"] = well
        measurement = import_measurement.import_measurement(session, measurement_row)

        # Experiments
        import_experiment.import_experiment(session, row_dict, well, measurement)

    session.commit()
    session.close()





BASE_PATH = r"/Users/pallottom/Documents/Projects/test_DB/data/"
FILES_CSV = r"/Users/pallottom\Documents/Projects/hi_dataB/ingestion_files.csv"

if __name__ == "__main__":
    df = pd.read_csv(FILES_CSV)

    for _, ingestion_row in df.iterrows(): #    for _, ingestion_row in df.iterrows():
        filename = ingestion_row.get("file_name")
        if pd.isna(filename) or filename is None:
            filename = ingestion_row.get("File_name")
        img_path = ingestion_row.get("img_path")
        if pd.isna(img_path):
            img_path = ""
        specimen_type = ingestion_row.get("specimen")
        if pd.isna(specimen_type) or specimen_type is None:
            specimen_type = "human"
        group_name = ingestion_row.get("group_name")
        if pd.isna(group_name):
            group_name = None
        project_name = ingestion_row.get("project_name")
        if pd.isna(project_name):
            project_name = None
        screen_description = ingestion_row.get("screen_description")
        if pd.isna(screen_description):
            screen_description = None
        full_path = os.path.join(BASE_PATH, filename)
        run_import(
            full_path,
            img_path=str(img_path),
            source_path=str(filename),
            specimen_type=str(specimen_type).strip().lower(),
            group_name=group_name,
            project_name=project_name,
            screen_description=screen_description,
            max_rows_per_file=50,  # Set to None to process all rows, or a number to limit for testing
        )

    print("✅ Data loading completed")


#""" "C:/Users/pallottom/Documents/Projects/screendb/screendb/test_data/metadata_import/IMXPR04S02_E01_wellinfo_20201202.csv" """
#""" ../test_DB/data/IMXPR04_postATP_ready4FeatureVector_JB_20220224 (copy).csv """
#"""../test_DB/data/IMXPR03S14R02R05_wi_htrf_asc_20251003_JB(in).csv""" # Mouse data
#"""../test_DB/data/GVS_20250822_extendedfeatures.csv""" # New Human data 
#"""../test_DB/data/IMXPR05S07R04R05_wi_htrf_icc_20250917_JB.csv""" # New Human data 