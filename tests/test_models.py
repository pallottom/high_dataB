import pytest

# Import model classes
from models import Project, Plate, Well, Specimen, HumanDonor, Measurement, Experiment


def test_models_have_tablenames():
	classes = [Project, Plate, Well, Specimen, HumanDonor, Measurement, Experiment]
	for cls in classes:
		assert hasattr(cls, "__tablename__"), f"{cls.__name__} missing __tablename__"
		assert isinstance(cls.__tablename__, str) and cls.__tablename__, "__tablename__ must be a non-empty string"


def test_models_define_primary_keys():
	# Verify each model's Table has at least one primary key column
	classes = [Project, Plate, Well, Specimen, HumanDonor, Measurement, Experiment]
	for cls in classes:
		table = getattr(cls, "__table__", None)
		assert table is not None, f"{cls.__name__} has no __table__"
		pk_cols = [c for c in table.columns if c.primary_key]
		assert pk_cols, f"{cls.__name__} table must define at least one primary key column"
