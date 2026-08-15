"""
Unit and integration test suite for metaheuristic algorithms and routing logic.
Covers:
1. Ant Colony Optimization (pheromone update, heuristic probability, convergence, data formats).
2. Genetic Algorithm & Memetic Algorithm (crossover, mutation, 2-opt local search, elitism).
3. Normalization and route rotation edge cases (single turbine, duplicate coords, Doca formatting).
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.ant_colony import AntColony
from scripts.genetic_algorithm import GeneticAlgorithm
from app.pages.ant_colony import min_max_scale


# ---------------------------------------------------------------------------
# Test Fixtures & Helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def square_turbines():
    """4 turbines placed at the corners of a unit square."""
    return [
        {'turbine_name': 'T0', 'latitude': 0.0, 'longitude': 0.0, 'latitude_norm': 0.0, 'longitude_norm': 0.0, 'fault_downtime_days': 0.0, 'fault_downtime_days_norm': 0.0},
        {'turbine_name': 'T1', 'latitude': 0.0, 'longitude': 1.0, 'latitude_norm': 0.0, 'longitude_norm': 1.0, 'fault_downtime_days': 0.0, 'fault_downtime_days_norm': 0.0},
        {'turbine_name': 'T2', 'latitude': 1.0, 'longitude': 1.0, 'latitude_norm': 1.0, 'longitude_norm': 1.0, 'fault_downtime_days': 0.0, 'fault_downtime_days_norm': 0.0},
        {'turbine_name': 'T3', 'latitude': 1.0, 'longitude': 0.0, 'latitude_norm': 1.0, 'longitude_norm': 0.0, 'fault_downtime_days': 0.0, 'fault_downtime_days_norm': 0.0},
    ]


@pytest.fixture
def sample_problem_dict():
    """5 turbines with varied positions and downtime costs in dict format."""
    return {
        0: {'turbine_name': 'Doca', 'latitude_norm': 0.0, 'longitude_norm': 0.0, 'fault_downtime_days_norm': 0.0},
        1: {'turbine_name': 'Turbine_A', 'latitude_norm': 0.2, 'longitude_norm': 0.8, 'fault_downtime_days_norm': 0.3},
        2: {'turbine_name': 'Turbine_B', 'latitude_norm': 0.5, 'longitude_norm': 0.5, 'fault_downtime_days_norm': 0.7},
        3: {'turbine_name': 'Turbine_C', 'latitude_norm': 0.9, 'longitude_norm': 0.1, 'fault_downtime_days_norm': 0.1},
        4: {'turbine_name': 'Turbine_D', 'latitude_norm': 0.7, 'longitude_norm': 0.9, 'fault_downtime_days_norm': 0.5},
    }


# ---------------------------------------------------------------------------
# Ant Colony Optimization (ACO) Tests
# ---------------------------------------------------------------------------

def test_aco_pheromone_update_non_uniform(square_turbines):
    """Verify that pheromone updates deposit pheromone on traversed edges, making pheromone non-uniform."""
    aco = AntColony(
        turbine_fault_list=square_turbines,
        n_ants=5,
        n_iterations=5,
        alpha=1.0,
        beta=2.0,
        evaporation_rate=0.3,
        Q=100.0
    )
    # Initially all pheromones are 1.0
    assert np.all(aco.pheromone == 1.0)

    aco.ant_colony_optimization()

    # After running, pheromone matrix should not be all equal
    assert not np.all(aco.pheromone == aco.pheromone[0, 0])
    assert np.all(aco.pheromone > 0)


def test_aco_finds_optimal_square_route(square_turbines):
    """4 points on a unit square should have optimal perimeter route length = 4.0."""
    np.random.seed(42)
    aco = AntColony(
        turbine_fault_list=square_turbines,
        n_ants=10,
        n_iterations=30,
        alpha=2.0,
        beta=3.0,
        evaporation_rate=0.5,
        Q=100.0
    )
    aco.ant_colony_optimization()

    assert aco.best_path is not None
    assert len(aco.best_path) == 5  # 4 nodes + return to start
    assert aco.best_path[0] == aco.best_path[-1]
    # Optimal square tour length is 4.0
    assert pytest.approx(aco.best_path_length, abs=1e-3) == 4.0
    # Every node from 0 to 3 should be visited once
    assert set(aco.best_path[:-1]) == {0, 1, 2, 3}


def test_aco_input_formats(sample_problem_dict):
    """Test that ACO supports dict of dicts, list of dicts, and numpy array inputs."""
    # Dict of dicts
    aco_dict = AntColony(sample_problem_dict, n_ants=4, n_iterations=5, alpha=1.0, beta=1.0, evaporation_rate=0.5, Q=10.0)
    aco_dict.ant_colony_optimization()
    assert aco_dict.best_path is not None
    assert len(aco_dict.turbine_order) == 6

    # List of dicts
    list_input = list(sample_problem_dict.values())
    aco_list = AntColony(list_input, n_ants=4, n_iterations=5, alpha=1.0, beta=1.0, evaporation_rate=0.5, Q=10.0)
    aco_list.ant_colony_optimization()
    assert aco_list.best_path is not None

    # Numpy array
    np_input = np.array([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]])
    aco_np = AntColony(np_input, n_ants=3, n_iterations=5, alpha=1.0, beta=1.0, evaporation_rate=0.5, Q=10.0)
    aco_np.ant_colony_optimization()
    assert aco_np.best_path is not None


def test_aco_single_and_two_turbines():
    """Verify ACO handles edge cases of 1 turbine and 2 turbines gracefully."""
    single = [{'turbine_name': 'Solo', 'latitude_norm': 0.5, 'longitude_norm': 0.5, 'fault_downtime_days_norm': 0.1}]
    aco_1 = AntColony(single, n_ants=2, n_iterations=5, alpha=1.0, beta=1.0, evaporation_rate=0.5, Q=10.0)
    aco_1.ant_colony_optimization()
    assert aco_1.best_path == [0, 0]
    assert aco_1.best_path_length == 0.0

    pair = [
        {'turbine_name': 'T1', 'latitude_norm': 0.0, 'longitude_norm': 0.0, 'fault_downtime_days_norm': 0.0},
        {'turbine_name': 'T2', 'latitude_norm': 0.0, 'longitude_norm': 1.0, 'fault_downtime_days_norm': 0.0}
    ]
    aco_2 = AntColony(pair, n_ants=2, n_iterations=5, alpha=1.0, beta=1.0, evaporation_rate=0.5, Q=10.0)
    aco_2.ant_colony_optimization()
    assert len(aco_2.best_path) == 3
    assert pytest.approx(aco_2.best_path_length, abs=1e-3) == 2.0


def test_aco_zero_distance_no_nan():
    """Verify ACO does not divide by zero or produce NaN when coordinates and downtimes are identical/zero."""
    identical = [
        {'turbine_name': 'A', 'latitude_norm': 0.0, 'longitude_norm': 0.0, 'fault_downtime_days_norm': 0.0},
        {'turbine_name': 'B', 'latitude_norm': 0.0, 'longitude_norm': 0.0, 'fault_downtime_days_norm': 0.0},
        {'turbine_name': 'C', 'latitude_norm': 0.0, 'longitude_norm': 0.0, 'fault_downtime_days_norm': 0.0}
    ]
    aco = AntColony(identical, n_ants=3, n_iterations=5, alpha=1.0, beta=2.0, evaporation_rate=0.5, Q=10.0)
    aco.ant_colony_optimization()
    assert not np.isnan(aco.best_path_length)
    assert not np.isnan(aco.best_downtime_days)
    assert not np.isnan(aco.best_path_len_downtime)


# ---------------------------------------------------------------------------
# Genetic & Memetic Algorithm Tests
# ---------------------------------------------------------------------------

def test_ga_crossover_valid_permutation(sample_problem_dict):
    """Verify that OX1 crossover always produces a valid permutation without missing or duplicated genes."""
    ga = GeneticAlgorithm(sample_problem_dict, population_size=10, n_generations=5, mutation_rate=0.1)
    parent1 = [0, 1, 2, 3, 4]
    parent2 = [4, 3, 2, 1, 0]

    for _ in range(50):
        child = ga.crossover(parent1, parent2)
        assert len(child) == 5
        assert set(child) == {0, 1, 2, 3, 4}
        assert -1 not in child


def test_ga_mutate_valid_permutation(sample_problem_dict):
    """Verify that mutation swaps genes while preserving the full set of vertices."""
    ga = GeneticAlgorithm(sample_problem_dict, population_size=10, n_generations=5, mutation_rate=1.0)
    ind = [0, 1, 2, 3, 4]
    mutated = ga.mutate(ind[:])
    assert set(mutated) == {0, 1, 2, 3, 4}
    assert len(mutated) == 5


def test_ga_two_opt_untangles_crossing():
    """Verify that 2-opt reverses crossed edges to improve tour length."""
    # 4 points on a square: order [0, 2, 1, 3] produces a self-crossing 'hourglass' (length 2 + 2*sqrt(2) ≈ 4.828)
    # Untangled perimeter route is [0, 1, 2, 3] (length 4.0)
    square = [
        {'turbine_name': 'T0', 'latitude_norm': 0.0, 'longitude_norm': 0.0, 'fault_downtime_days_norm': 0.0},
        {'turbine_name': 'T1', 'latitude_norm': 0.0, 'longitude_norm': 1.0, 'fault_downtime_days_norm': 0.0},
        {'turbine_name': 'T2', 'latitude_norm': 1.0, 'longitude_norm': 1.0, 'fault_downtime_days_norm': 0.0},
        {'turbine_name': 'T3', 'latitude_norm': 1.0, 'longitude_norm': 0.0, 'fault_downtime_days_norm': 0.0},
    ]
    ga = GeneticAlgorithm(square, population_size=10, n_generations=1, mutation_rate=0.0, implement_local_search=True)

    crossed_route = [0, 2, 1, 3]
    initial_dist = ga.calculate_total_distance(crossed_route)
    improved_route = ga.two_opt(crossed_route)
    improved_dist = ga.calculate_total_distance(improved_route)

    assert set(improved_route) == {0, 1, 2, 3}
    assert improved_dist < initial_dist
    assert pytest.approx(improved_dist, abs=1e-3) == 4.0


def test_ga_memetic_evolve_finds_square_optimal(square_turbines):
    """Verify that Memetic algorithm (GA + 2-opt) solves 4-point square optimally."""
    ga = GeneticAlgorithm(
        turbine_fault_list=square_turbines,
        population_size=20,
        n_generations=20,
        mutation_rate=0.1,
        implement_local_search=True
    )
    ga.evolve()

    assert ga.best_path is not None
    assert len(ga.best_path) == 5
    assert ga.best_path[0] == ga.best_path[-1]
    assert pytest.approx(ga.best_path_length, abs=1e-3) == 4.0


def test_ga_selection_evaluates_closed_loop():
    """Verify that selection evaluates closed cycles, not just open segments."""
    turbines = [
        {'turbine_name': 'T0', 'latitude_norm': 0.0, 'longitude_norm': 0.0, 'fault_downtime_days_norm': 0.0},
        {'turbine_name': 'T1', 'latitude_norm': 0.0, 'longitude_norm': 1.0, 'fault_downtime_days_norm': 0.0},
        {'turbine_name': 'T2', 'latitude_norm': 10.0, 'longitude_norm': 10.0, 'fault_downtime_days_norm': 0.0},
    ]
    ga = GeneticAlgorithm(turbines, population_size=4, n_generations=1, mutation_rate=0.0)

    # Route [0, 1, 2]: open length is dist(0,1) + dist(1,2) ≈ 1 + 12.72 = 13.72
    # Closed length is dist(0,1) + dist(1,2) + dist(2,0) ≈ 1 + 12.72 + 14.14 = 27.87
    dist, _ = ga.objective_function([0, 1, 2])
    assert dist > 20.0  # Must include return edge


def test_ga_single_and_two_turbines():
    """Verify GA handles small instances (N=1, N=2) without index/sample errors."""
    single = [{'turbine_name': 'Solo', 'latitude_norm': 0.5, 'longitude_norm': 0.5, 'fault_downtime_days_norm': 0.1}]
    ga_1 = GeneticAlgorithm(single, population_size=10, n_generations=5, mutation_rate=0.1)
    ga_1.evolve()
    assert ga_1.best_path == [0, 0]
    assert ga_1.best_path_length == 0.0

    pair = [
        {'turbine_name': 'T1', 'latitude_norm': 0.0, 'longitude_norm': 0.0, 'fault_downtime_days_norm': 0.0},
        {'turbine_name': 'T2', 'latitude_norm': 0.0, 'longitude_norm': 1.0, 'fault_downtime_days_norm': 0.0}
    ]
    ga_2 = GeneticAlgorithm(pair, population_size=10, n_generations=5, mutation_rate=0.1)
    ga_2.evolve()
    assert len(ga_2.best_path) == 3
    assert pytest.approx(ga_2.best_path_length, abs=1e-3) == 2.0


# ---------------------------------------------------------------------------
# Normalization & Route Rotation Tests
# ---------------------------------------------------------------------------

def test_min_max_scale_safe_constant_series():
    """Verify min_max_scale returns 0.0 when max == min instead of NaN."""
    s = pd.Series([5.0, 5.0, 5.0])
    scaled = min_max_scale(s)
    assert not scaled.isna().any()
    assert (scaled == 0.0).all()

    s_single = pd.Series([10.0])
    scaled_single = min_max_scale(s_single)
    assert not scaled_single.isna().any()
    assert scaled_single.iloc[0] == 0.0


def test_min_max_scale_normal_range():
    """Verify min_max_scale properly maps values to [0, 1]."""
    s = pd.Series([10.0, 20.0, 30.0])
    scaled = min_max_scale(s)
    assert pytest.approx(scaled.iloc[0]) == 0.0
    assert pytest.approx(scaled.iloc[1]) == 0.5
    assert pytest.approx(scaled.iloc[2]) == 1.0


def test_route_rotation_no_duplicate_turbines():
    """Verify route rotation places Doca at start and end without duplicating internal turbines."""
    # Test cases:
    cases = [
        # Doca at beginning of closed loop
        ['Doca', 'T1', 'T2', 'Doca'],
        # Doca in middle of closed loop
        ['T1', 'Doca', 'T2', 'T1'],
        # Doca at end of cycle before return
        ['T1', 'T2', 'Doca', 'T1'],
    ]

    for turbine_order in cases:
        if len(turbine_order) > 1 and turbine_order[0] == turbine_order[-1]:
            unique_nodes = turbine_order[:-1]
        else:
            unique_nodes = turbine_order[:]

        if "Doca" in unique_nodes:
            doca_idx = unique_nodes.index("Doca")
            ordered_nodes = unique_nodes[doca_idx:] + unique_nodes[:doca_idx]
            to_show = [*ordered_nodes, "Doca"]
        else:
            to_show = ["Doca", *unique_nodes, "Doca"]

        assert to_show[0] == "Doca"
        assert to_show[-1] == "Doca"
        # Each non-Doca turbine must appear exactly once
        assert to_show.count("T1") == 1
        assert to_show.count("T2") == 1
        assert to_show.count("Doca") == 2
        assert len(to_show) == 4
