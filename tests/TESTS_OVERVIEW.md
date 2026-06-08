# Test Suite Overview

This document explains the purpose of the tests in this folder, grouped by test file.

## Shared Test Setup

The shared setup lives in `conftest.py`.

- The test environment is selected with `ENVIRONMENT=tests` by default.
- `db_engine` checks database connectivity first.
- If the database cannot be reached, database-backed tests are skipped.
- `db_session` provides a clean SQLAlchemy session per test.
- Tables are truncated between tests to keep tests isolated and repeatable.

## Importers Tests (`test_importers.py`)

These tests check that importer functions clean and standardize data, create the right records, and avoid creating duplicates when you import the same data again.

- `test_import_management_idempotent`
  - Imports project, screen, plate, and location twice.
  - Verifies the second import reuses existing rows instead of creating duplicates.
- `test_import_specimen_and_well_normalization`
  - Imports a specimen and then the same well using two key formats (`a1` and `A01`).
  - Verifies well-key normalization and no duplicate well row creation.
- `test_import_specimen_duplicate_reuses_existing_record`
  - Imports the same specimen twice using the same donor identity.
  - Verifies the importer reuses the existing specimen record instead of creating a duplicate.
  - Verifies related fields (such as anticoagulant) can be updated on repeated import.
- `test_import_experiment_creates_condition_and_treatments`
  - Imports experiment data for a well.
  - Verifies condition class, treatments, and experiment rows are created correctly.
  - Verifies the well QC status is updated as expected.
- `test_import_experiment_duplicate_reuses_existing_record`
  - Imports the same experiment payload twice for the same well.
  - Verifies the existing experiment record is reused.
  - Verifies treatment rows are not duplicated.
- `test_import_plate_missing_required_barcode_raises`
  - Attempts to import a plate without a barcode.
  - Verifies the importer raises a clear `ValueError` for missing required input.
- `test_import_plate_invalid_date_format_is_stored_as_string`
  - Imports a plate with a non-date value in `date_experiment`.
  - Verifies the importer stores the value as a raw string instead of crashing.
- `test_import_experiment_invalid_concentration_unit_raises`
  - Attempts to import experiment treatment data with an invalid concentration unit.
  - Verifies database validation rejects the row during commit.
- `test_import_well_invalid_key_raises`
  - Attempts to import an invalid well key.
  - Verifies a `ValueError` path and rollback behavior.

Note on invalid-input assertions:
- Some invalid inputs are expected to be rejected immediately (for example, missing barcode and invalid well key).
- Some invalid inputs are expected to be rejected by database constraints at commit time (for example, invalid concentration units).
- Some malformed values are currently accepted and stored as provided (for example, non-date text in `date_experiment`).

## Models Tests (`test_models.py`)

These tests check model metadata, integrity constraints, and relationship behavior.

- `test_models_have_tablenames`
  - Verifies key model classes define non-empty `__tablename__` values.
- `test_models_define_primary_keys`
  - Verifies key model tables define at least one primary key.
- `test_screen_number_unique_per_project`
  - Verifies uniqueness of `screen_number` within a project.
  - Expects an integrity error when inserting a duplicate.
- `test_plate_barcode_format_constraint`
  - Verifies invalid barcode values are rejected by schema constraints.
- `test_well_unique_key_per_plate_and_relationships`
  - Verifies per-plate uniqueness of `well_key` and relationship wiring.
  - Expects an integrity error on duplicate well insertion.

## Schema Tests (`test_schema.py`)

These tests validate database availability and expected schema presence.

- `test_configured_test_database_exists`
  - Connects to the maintenance database (`postgres`) using current DB credentials.
  - Checks whether the configured target database name exists in `pg_database`.
  - Fails with a clear message if the configured test database is missing.
- `test_db_connection`
  - Verifies a basic `SELECT 1` succeeds against the configured test database.
- `test_required_tables_exist`
  - Verifies all expected tables exist in the configured test database.

## Interpreting Pass/Skip/Fail Quickly

- Passed: Test assertions and DB operations succeeded.
- Skipped: Usually indicates DB connectivity setup is missing for DB-backed tests.
- Failed: Assertions, schema expectations, or constraints did not match expected behavior.

## Typical Setup Before Running Tests

1. Activate the virtual environment.
2. Ensure `ENVIRONMENT=tests` is set in your shell.
3. Ensure the configured test database exists and is reachable (in `config.toml` check `host`, `port`, `name`, and `user`).
4. Run `python -m pytest -rs`.
