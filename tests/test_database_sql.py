"""
Unit and Integration Tests for Database SQL Generation and Query Compatibility.

Tests that:
1. database.sql is properly generated from database/ CSVs.
2. The generated SQL script executes without error on SQLite / PostgreSQL.
3. app.crud functions (get_turbines_map, get_subsystems, get_downtimes) run successfully
   against a database initialized with the generated .sql file.
"""

import os
import sys
import sqlite3
import pytest
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from tests.generate_sql import build_sql_script, verify_sql_script, DATABASE_DIR
from app import crud


@pytest.fixture(scope="module")
def sql_content():
    """Build and return the generated SQL script content."""
    return build_sql_script(DATABASE_DIR)


@pytest.fixture
def db_session(sql_content):
    """Provide an in-memory SQLite SQLAlchemy Session seeded with the generated SQL script."""
    engine = create_engine("sqlite:///:memory:")

    # Execute raw SQL script to seed schema and data
    raw_conn = engine.raw_connection()
    try:
        raw_conn.executescript(sql_content)
        raw_conn.commit()
    finally:
        raw_conn.close()

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_sql_generation(sql_content):
    """Verify that build_sql_script generates non-empty SQL content containing expected DDL/DML."""
    assert "CREATE TABLE IF NOT EXISTS subsystem" in sql_content
    assert "CREATE TABLE IF NOT EXISTS wind_farm_map_points" in sql_content
    assert "CREATE TABLE IF NOT EXISTS downtime" in sql_content
    assert "INSERT INTO subsystem" in sql_content
    assert "INSERT INTO wind_farm_map_points" in sql_content
    assert "INSERT INTO downtime" in sql_content


def test_sql_script_execution(sql_content):
    """Verify that verify_sql_script returns True for SQLite in-memory execution."""
    assert verify_sql_script(sql_content) is True


def test_crud_get_turbines_map(db_session):
    """Verify app.crud.get_turbines_map works on database populated with SQL script."""
    turbines = crud.get_turbines_map(db_session)
    assert len(turbines) == 213
    first_turbine = dict(turbines[0]._mapping)
    assert first_turbine["turbine_id"] == 1
    assert first_turbine["turbine_name"] == "Doca"


def test_crud_get_subsystems(db_session):
    """Verify app.crud.get_subsystems works on database populated with SQL script."""
    subsystems = crud.get_subsystems(db_session)
    assert len(subsystems) == 11
    first_sub = dict(subsystems[0]._mapping)
    assert first_sub["subsystem_id"] == 1
    assert first_sub["subsystem_name"] == "Electrical System"


def test_crud_get_downtimes(db_session):
    """Verify app.crud.get_downtimes works on database populated with SQL script."""
    downtimes = crud.get_downtimes(db_session)
    # 11 subsystems in subsystem table with 2 downtime entries each = 22 joined rows
    assert len(downtimes) == 22
    first_downtime = dict(downtimes[0]._mapping)
    assert first_downtime["subsystem_id"] == 1
    assert first_downtime["subsystem_name"] == "Electrical System"
    assert first_downtime["fault_type"] in ["Minor", "Major"]
