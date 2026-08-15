"""
Integration tests for FastAPI endpoints.
Verifies GET /get-turbines-map, GET /get-subsystems, and POST /run-route-optimizer.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_turbines_map():
    response = client.get("/ant-colony/get-turbines-map")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "turbine_id" in data[0]
    assert "turbine_name" in data[0]
    assert "latitude" in data[0]
    assert "longitude" in data[0]


def test_get_subsystems():
    response = client.get("/ant-colony/get-subsystems")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "subsystem_id" in data[0]
    assert "subsystem_name" in data[0]


def test_run_route_optimizer_ant_colony():
    payload = [
        {"turbine_id": 2, "subsystem_name": "Electrical System", "fault_type": "Minor"},
        {"turbine_id": 3, "subsystem_name": "Rotor Hub", "fault_type": "Major"}
    ]
    response = client.post("/ant-colony/run-route-optimizer?algorithm=Ant Colony", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "turbine_order" in data
    assert "best_path_length" in data
    assert "best_downtime_days" in data
    assert "time_to_run_sec" in data


def test_run_route_optimizer_genetic():
    payload = [
        {"turbine_id": 2, "subsystem_name": "Electrical System", "fault_type": "Minor"},
        {"turbine_id": 3, "subsystem_name": "Rotor Hub", "fault_type": "Major"}
    ]
    response = client.post("/ant-colony/run-route-optimizer?algorithm=Genetic", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "turbine_order" in data


def test_run_route_optimizer_memetic():
    payload = [
        {"turbine_id": 2, "subsystem_name": "Electrical System", "fault_type": "Minor"},
        {"turbine_id": 3, "subsystem_name": "Rotor Hub", "fault_type": "Major"}
    ]
    response = client.post("/ant-colony/run-route-optimizer?algorithm=Memetic", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "turbine_order" in data
    assert "turbine_order_to_show" in data
    assert data["turbine_order_to_show"][0] == "Doca"
    assert data["turbine_order_to_show"][-1] == "Doca"


def test_run_route_optimizer_single_turbine():
    """Verify endpoint handles a single turbine fault without division-by-zero or NaN."""
    payload = [
        {"turbine_id": 2, "subsystem_name": "Electrical System", "fault_type": "Minor"}
    ]
    response = client.post("/ant-colony/run-route-optimizer?algorithm=Ant Colony", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["turbine_order_to_show"][0] == "Doca"
    assert data["turbine_order_to_show"][-1] == "Doca"
    assert len(data["turbine_order_to_show"]) == 3  # Doca -> BETA-01 -> Doca


def test_run_route_optimizer_empty_payload():
    """Verify endpoint handles empty list by falling back to default problem dataset."""
    response = client.post("/ant-colony/run-route-optimizer?algorithm=Genetic", json=[])
    assert response.status_code == 200
    data = response.json()
    assert len(data["turbine_order_to_show"]) > 0
    assert data["turbine_order_to_show"][0] == "Doca"
    assert data["turbine_order_to_show"][-1] == "Doca"
