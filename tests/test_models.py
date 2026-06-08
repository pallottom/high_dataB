import pytest
from sqlalchemy.exc import IntegrityError

from models import (
	CellCharacteristics,
	CellType,
	HumanDonor,
	Plate,
	Project,
	Screen,
	Specimen,
	Well,
	MeasurementValue,
	Experiment,
)


def _create_plate(db_session, barcode="AAAPR01S01R01p01"):
	project = Project(group_name="AAA", name="project AAA")
	screen = Screen(screen_number=1, screen_description="screen 1", project=project)
	plate = Plate(name="plate_1", barcode=barcode, date_experiment="2026-06-01", screen=screen)
	db_session.add(plate)
	db_session.commit()
	return plate


def _create_human_donor(db_session, donor_name="donor_1"):
	cell_type = CellType(name="PBMC")
	cell_characteristic = CellCharacteristics(name="Primary")
	donor = HumanDonor(name=donor_name, cell_type=cell_type, cell_characteristic=cell_characteristic)
	db_session.add(donor)
	db_session.commit()
	return donor


def test_models_have_tablenames():
	classes = [Project, Plate, Well, Specimen, HumanDonor, MeasurementValue, Experiment]
	for cls in classes:
		assert hasattr(cls, "__tablename__"), f"{cls.__name__} missing __tablename__"
		assert isinstance(cls.__tablename__, str) and cls.__tablename__, "__tablename__ must be a non-empty string"


def test_models_define_primary_keys():
	classes = [Project, Plate, Well, Specimen, HumanDonor, MeasurementValue, Experiment]
	for cls in classes:
		table = getattr(cls, "__table__", None)
		assert table is not None, f"{cls.__name__} has no __table__"
		pk_cols = [c for c in table.columns if c.primary_key]
		assert pk_cols, f"{cls.__name__} table must define at least one primary key column"


def test_screen_number_unique_per_project(db_session):
	project = Project(group_name="BBB", name="project BBB")
	db_session.add(project)
	db_session.flush()

	db_session.add(Screen(screen_number=7, project=project))
	db_session.commit()

	db_session.add(Screen(screen_number=7, project=project))
	with pytest.raises(IntegrityError):
		db_session.commit()


def test_plate_barcode_format_constraint(db_session):
	project = Project(group_name="CCC", name="project CCC")
	screen = Screen(screen_number=1, project=project)
	db_session.add_all([project, screen])
	db_session.flush()

	db_session.add(Plate(name="bad_plate", barcode="INVALID", date_experiment="2026-06-01", screen=screen))
	with pytest.raises(IntegrityError):
		db_session.commit()


def test_well_unique_key_per_plate_and_relationships(db_session):
	plate = _create_plate(db_session)
	donor = _create_human_donor(db_session)

	db_session.add(Well(well_key="A01", plate=plate, specimen=donor))
	db_session.commit()

	assert len(plate.wells) == 1
	assert len(donor.wells) == 1

	db_session.add(Well(well_key="A01", plate=plate, specimen=donor))
	with pytest.raises(IntegrityError):
		db_session.commit()
