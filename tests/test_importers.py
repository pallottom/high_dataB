import pytest
from sqlalchemy.exc import DataError, IntegrityError

from importers.import_experiment import import_experiment
from importers.import_management import import_location, import_plate, import_project, import_screen
from importers.import_specimen import import_specimen
from importers.import_wells import import_well
from models import ConditionClass, Experiment, Plate, Project, Screen, Specimen, Treatment, Well


def test_import_management_idempotent(db_session):
    project = import_project(db_session, group_name="AAA", project_name="project AAA")
    screen = import_screen(db_session, project, screen_number=1, description="test screen")
    plate = import_plate(
        db_session,
        screen,
        name="plate 1",
        barcode="AAAPR01S01R01p01",
        date_experiment="2026-06-01",
    )
    location = import_location(db_session, plate, img_path="//server/test.csv", source_path="//server")
    db_session.commit()

    # Import the same records again and ensure no duplicates are created.
    project_2 = import_project(db_session, group_name="AAA", project_name="project AAA")
    screen_2 = import_screen(db_session, project_2, screen_number=1, description="test screen")
    plate_2 = import_plate(
        db_session,
        screen_2,
        name="plate 1",
        barcode="AAAPR01S01R01p01",
        date_experiment="2026-06-01",
    )
    location_2 = import_location(db_session, plate_2, img_path="//server/test.csv", source_path="//server")
    db_session.commit()

    assert project.id == project_2.id
    assert screen.id == screen_2.id
    assert plate.id == plate_2.id
    assert location.id == location_2.id
    assert db_session.query(Project).count() == 1
    assert db_session.query(Screen).count() == 1
    assert db_session.query(Plate).count() == 1


def test_import_specimen_and_well_normalization(db_session):
    project = import_project(db_session, group_name="BBB", project_name="project BBB")
    screen = import_screen(db_session, project, screen_number=2, description="screen")
    plate = import_plate(
        db_session,
        screen,
        name="plate 2",
        barcode="BBBPR01S02R01p01",
        date_experiment="2026-06-01",
    )

    specimen = import_specimen(
        db_session,
        {
            "specimen": "human",
            "donor_loc": "DNR_001",
            "cell_type": "PBMC",
            "cell_characteristic": "Primary",
            "anticoagulant": "EDTA",
            "age": "42",
            "sex": "F",
        },
    )

    well_1 = import_well(db_session, plate, "a1", specimen)
    db_session.commit()

    well_2 = import_well(db_session, plate, "A01", specimen)
    db_session.commit()

    assert specimen.id is not None
    assert db_session.query(Specimen).count() == 1
    assert well_1.id == well_2.id
    assert well_1.well_key == "A01"
    assert db_session.query(Well).count() == 1


def test_import_specimen_duplicate_reuses_existing_record(db_session):
    specimen_1 = import_specimen(
        db_session,
        {
            "specimen": "human",
            "donor_loc": "DNR_DUP_001",
            "cell_type": "PBMC",
            "cell_characteristic": "Primary",
            "anticoagulant": "EDTA",
            "age": "42",
            "sex": "F",
        },
    )
    db_session.commit()

    specimen_2 = import_specimen(
        db_session,
        {
            "specimen": "human",
            "donor_loc": "DNR_DUP_001",
            "cell_type": "PBMC",
            "cell_characteristic": "Primary",
            "anticoagulant": "Heparin",
            "age": "99",
            "sex": "F",
        },
    )
    db_session.commit()

    assert specimen_1.id == specimen_2.id
    assert db_session.query(Specimen).count() == 1
    assert specimen_2.anticoagulant is not None
    assert specimen_2.anticoagulant.anticoagulant_name == "Heparin"


def test_import_experiment_creates_condition_and_treatments(db_session):
    project = import_project(db_session, group_name="CCC", project_name="project CCC")
    screen = import_screen(db_session, project, screen_number=3, description="screen")
    plate = import_plate(
        db_session,
        screen,
        name="plate 3",
        barcode="CCCPR01S03R01p01",
        date_experiment="2026-06-01",
    )
    specimen = import_specimen(
        db_session,
        {
            "specimen": "human",
            "donor_loc": "DNR_002",
            "cell_type": "PBMC",
            "cell_characteristic": "Primary",
            "anticoagulant": "Heparin",
        },
    )
    well = import_well(db_session, plate, "B12", specimen)

    experiment = import_experiment(
        db_session,
        {
            "condition_class": "sample_prim_activ",
            "prim_name": "LPS",
            "prim_conc": 10,
            "prim_conc_unit": "nM",
            "prim_time_min": 30,
            "activ_name": "ATP",
            "activ_conc": 5,
            "activ_conc_unit": "nM",
            "activ_time_min": 15,
            "htrf_il1b_data": 1.23,
            "htrf_tnfa_data": None,
        },
        well,
        measurement=None,
    )
    db_session.commit()

    assert experiment is not None
    assert db_session.query(ConditionClass).count() == 1
    assert db_session.query(Treatment).count() == 2
    assert db_session.query(Experiment).count() == 1
    assert well.qc == "pass"


def test_import_experiment_duplicate_reuses_existing_record(db_session):
    project = import_project(db_session, group_name="EEE", project_name="project EEE")
    screen = import_screen(db_session, project, screen_number=5, description="screen")
    plate = import_plate(
        db_session,
        screen,
        name="plate 5",
        barcode="EEEPR01S05R01p01",
        date_experiment="2026-06-01",
    )
    specimen = import_specimen(
        db_session,
        {
            "specimen": "human",
            "donor_loc": "DNR_005",
            "cell_type": "PBMC",
            "cell_characteristic": "Primary",
            "anticoagulant": "EDTA",
        },
    )
    well = import_well(db_session, plate, "C05", specimen)

    row = {
        "condition_class": "sample_prim_activ",
        "prim_name": "LPS",
        "prim_conc": 10,
        "prim_conc_unit": "nM",
        "prim_time_min": 30,
        "activ_name": "ATP",
        "activ_conc": 5,
        "activ_conc_unit": "nM",
        "activ_time_min": 15,
        "htrf_il1b_data": 1.23,
        "htrf_tnfa_data": None,
    }

    experiment_1 = import_experiment(db_session, row, well, measurement=None)
    db_session.commit()

    experiment_2 = import_experiment(db_session, row, well, measurement=None)
    db_session.commit()

    assert experiment_1.id == experiment_2.id
    assert db_session.query(Experiment).count() == 1
    assert db_session.query(Treatment).count() == 2
    assert well.qc == "pass"


def test_import_plate_missing_required_barcode_raises(db_session):
    project = import_project(db_session, group_name="FFF", project_name="project FFF")
    screen = import_screen(db_session, project, screen_number=6, description="screen")

    with pytest.raises(ValueError, match="Plate barcode is required"):
        import_plate(
            db_session,
            screen,
            name="plate 6",
            barcode="",
            date_experiment="2026-06-01",
        )


def test_import_plate_invalid_date_format_is_stored_as_string(db_session):
    project = import_project(db_session, group_name="GGG", project_name="project GGG")
    screen = import_screen(db_session, project, screen_number=7, description="screen")

    plate = import_plate(
        db_session,
        screen,
        name="plate 7",
        barcode="GGGPR01S07R01p01",
        date_experiment="not-a-date",
    )
    db_session.commit()

    stored_plate = db_session.query(Plate).filter_by(barcode="GGGPR01S07R01p01").first()
    assert stored_plate is not None
    assert stored_plate.date_experiment == "not-a-date"


def test_import_experiment_invalid_concentration_unit_raises(db_session):
    project = import_project(db_session, group_name="HHH", project_name="project HHH")
    screen = import_screen(db_session, project, screen_number=8, description="screen")
    plate = import_plate(
        db_session,
        screen,
        name="plate 8",
        barcode="HHHPR01S08R01p01",
        date_experiment="2026-06-01",
    )
    specimen = import_specimen(
        db_session,
        {
            "specimen": "human",
            "donor_loc": "DNR_008",
            "cell_type": "PBMC",
            "cell_characteristic": "Primary",
            "anticoagulant": "EDTA",
        },
    )
    well = import_well(db_session, plate, "D06", specimen)

    with pytest.raises((IntegrityError, DataError)):
        import_experiment(
            db_session,
            {
                "condition_class": "sample_invalid_unit",
                "prim_name": "LPS",
                "prim_conc": 10,
                "prim_conc_unit": "ppm",
                "prim_time_min": 30,
                "activ_name": None,
                "htrf_il1b_data": 1.23,
                "htrf_tnfa_data": None,
            },
            well,
            measurement=None,
        )
        db_session.commit()

    db_session.rollback()


def test_import_well_invalid_key_raises(db_session):
    project = import_project(db_session, group_name="DDD", project_name="project DDD")
    screen = import_screen(db_session, project, screen_number=4, description="screen")
    plate = import_plate(
        db_session,
        screen,
        name="plate 4",
        barcode="DDDPR01S04R01p01",
        date_experiment="2026-06-01",
    )
    specimen = import_specimen(
        db_session,
        {
            "specimen": "human",
            "donor_loc": "DNR_003",
            "cell_type": "PBMC",
            "cell_characteristic": "Primary",
        },
    )

    try:
        import_well(db_session, plate, "Q99", specimen)
        db_session.commit()
        assert False, "Expected ValueError for invalid well key"
    except ValueError:
        db_session.rollback()
