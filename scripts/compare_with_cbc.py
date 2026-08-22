import pandas as pd
import numpy as np
import time
import pulp
import os
import json
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))
sys.path.insert(0, str(BASE_DIR))

from scripts.ant_colony import AntColony
from scripts.genetic_algorithm import GeneticAlgorithm

TIMEOUT_PER_PROBLEM_SEC = 300  # 5 minutes limit per algorithm per problem

PROBLEMS = [
    ("Problem 1 (5 Turbines)", str(BASE_DIR / "tests" / "inputs" / "problem_5_turbines.csv"), 5),
    ("Problem 2 (10 Turbines)", str(BASE_DIR / "tests" / "inputs" / "problem_10_turbines.csv"), 10),
    ("Problem 3 (15 Turbines)", str(BASE_DIR / "tests" / "inputs" / "problem_15_turbines.csv"), 15),
    ("Problem 4 (20 Turbines)", str(BASE_DIR / "tests" / "inputs" / "problem_20_turbines.csv"), 20),
    ("Problem 5 (40 Turbines)", str(BASE_DIR / "tests" / "inputs" / "problem_40_turbines.csv"), 40),
    ("Problem 6 (100 Turbines)", str(BASE_DIR / "tests" / "inputs" / "problem_100_turbines.csv"), 100),
    ("Problem 7 (200 Turbines)", str(BASE_DIR / "tests" / "inputs" / "problem_200_turbines.csv"), 200),
]


def min_max_scale(series: pd.Series) -> pd.Series:
    s_min = series.min()
    s_max = series.max()
    denom = s_max - s_min
    if denom == 0 or pd.isna(denom):
        return pd.Series(0.0, index=series.index)
    return (series - s_min) / denom


def load_problem_data(file_path: str):
    df = pd.read_csv(file_path, index_col=0).reset_index(drop=True)
    df["latitude_norm"] = min_max_scale(df["latitude"])
    df["longitude_norm"] = min_max_scale(df["longitude"])
    if "fault_downtime_days_norm" not in df.columns:
        df["fault_downtime_days_norm"] = min_max_scale(df.get("fault_downtime_days", pd.Series(0.0, index=df.index)))
    
    pts = df[["latitude_norm", "longitude_norm"]].values
    dts = df["fault_downtime_days_norm"].values
    names = df["turbine_name"].tolist() if "turbine_name" in df.columns else [f"Point_{i}" for i in range(len(df))]
    data_dict = df.to_dict("index")
    return df, pts, dts, names, data_dict


def solve_cbc(points: np.ndarray, dts: np.ndarray, names: list, max_seconds: int = TIMEOUT_PER_PROBLEM_SEC):
    """
    Solves the exact TSP with Downtime Objective using Coin-OR CBC via PuLP
    with iterative subtour elimination constraints (Dantzig-Fulkerson-Johnson / DFJ).
    """
    n = len(points)
    dist_matrix = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(n):
            if i != j:
                dist = float(np.linalg.norm(points[i] - points[j]))
                dt = float(dts[i] + dts[j])
                dist_matrix[i, j] = dist + dt

    prob = pulp.LpProblem("TSP_Downtime_CBC", pulp.LpMinimize)
    x = pulp.LpVariable.dicts("x", ((i, j) for i in range(n) for j in range(n) if i != j), cat=pulp.LpBinary)

    # Objective: Minimize total edge cost (scaled distance + downtime cost)
    prob += pulp.lpSum(dist_matrix[i, j] * x[i, j] for i in range(n) for j in range(n) if i != j)

    # In-degree and Out-degree constraints (each node visited exactly once)
    for i in range(n):
        prob += pulp.lpSum(x[i, j] for j in range(n) if j != i) == 1
    for j in range(n):
        prob += pulp.lpSum(x[i, j] for i in range(n) if i != j) == 1

    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=max_seconds, threads=4)
    
    start_time = time.time()
    iteration = 0
    while True:
        iteration += 1
        elapsed = time.time() - start_time
        remaining_time = max_seconds - elapsed
        if remaining_time <= 0:
            break
        
        solver.timeLimit = max(1, int(remaining_time))
        prob.solve(solver)
        
        # Build successor map
        succ = {}
        for i in range(n):
            for j in range(n):
                if i != j and pulp.value(x[i, j]) is not None and pulp.value(x[i, j]) > 0.5:
                    succ[i] = j

        # Identify all disjoint cycles
        visited = [False] * n
        cycles = []
        for i in range(n):
            if not visited[i]:
                cycle = []
                curr = i
                while not visited[curr]:
                    visited[curr] = True
                    cycle.append(curr)
                    curr = succ.get(curr, curr)
                if cycle and succ.get(cycle[-1]) == cycle[0]:
                    cycles.append(cycle)

        # If exactly one cycle of length N is found, it is the globally optimal Hamiltonian tour!
        if len(cycles) == 1 and len(cycles[0]) == n:
            tour = cycles[0] + [cycles[0][0]]
            solve_time = time.time() - start_time
            obj_val = pulp.value(prob.objective)
            total_dist = sum(np.linalg.norm(points[tour[k]] - points[tour[k + 1]]) for k in range(len(tour) - 1))
            total_dt = sum(dts[tour[k]] + dts[tour[k + 1]] for k in range(len(tour) - 1))
            
            # Rotate tour so Doca (node 0) is at start and end
            doca_idx = tour.index(0) if 0 in tour else 0
            rotated_tour = tour[doca_idx:-1] + tour[:doca_idx] + [0]
            turbine_order = [names[idx] for idx in rotated_tour]
            
            return {
                "status": "Optimal",
                "cost": float(obj_val),
                "distance": float(total_dist),
                "downtime": float(total_dt),
                "time_sec": float(solve_time),
                "iterations": iteration,
                "tour": rotated_tour,
                "turbine_order": turbine_order
            }

        # Add subtour elimination cuts
        for cycle in cycles:
            if len(cycle) < n:
                prob += pulp.lpSum(x[i, j] for i in cycle for j in cycle if i != j) <= len(cycle) - 1

    # Fallback if timeout reached
    solve_time = time.time() - start_time
    return {
        "status": "TimeLimit",
        "cost": float(pulp.value(prob.objective) or np.nan),
        "distance": np.nan,
        "downtime": np.nan,
        "time_sec": float(solve_time),
        "iterations": iteration,
        "tour": [],
        "turbine_order": []
    }


def run_aco_trials(data_dict: dict, n_turbines: int, max_seconds: int = TIMEOUT_PER_PROBLEM_SEC, n_trials: int = 5):
    if n_turbines <= 10:
        n_ants = 3
        alpha = 5.0
        beta = 1.5
        rho = 0.5
        n_iterations = 200
    elif n_turbines <= 40:
        n_ants = 8
        alpha = 5.0
        beta = 2.0
        rho = 0.5
        n_iterations = 200
    else:
        n_ants = 10
        alpha = 5.0
        beta = 2.0
        rho = 0.5
        n_iterations = 100

    costs, times, dists = [], [], []
    best_obj = None
    t_start = time.time()

    for seed in range(n_trials):
        if time.time() - t_start >= max_seconds:
            break
        np.random.seed(seed * 42 + 7)
        t0 = time.time()
        aco = AntColony(
            data_dict,
            n_ants=n_ants,
            n_iterations=n_iterations,
            alpha=alpha,
            beta=beta,
            evaporation_rate=rho,
            Q=100.0
        )
        aco.ant_colony_optimization()
        t1 = time.time() - t0
        costs.append(aco.best_path_len_downtime)
        times.append(t1)
        dists.append(aco.best_path_length)
        if best_obj is None or aco.best_path_len_downtime < best_obj["cost"]:
            best_obj = {
                "cost": aco.best_path_len_downtime,
                "distance": aco.best_path_length,
                "downtime": aco.best_downtime_days,
                "time_sec": t1,
                "tour": aco.best_path,
                "turbine_order": aco.turbine_order
            }

    return {
        "best_cost": float(min(costs)),
        "mean_cost": float(np.mean(costs)),
        "std_cost": float(np.std(costs)),
        "best_time": float(min(times)),
        "mean_time": float(np.mean(times)),
        "best_dist": float(min(dists)),
        "best_obj": best_obj
    }


def run_ga_trials(data_dict: dict, n_turbines: int, max_seconds: int = TIMEOUT_PER_PROBLEM_SEC, n_trials: int = 5):
    if n_turbines >= 15:
        mutation_rate = 0.1
        population_size = 100
        n_generations = 50
    else:
        mutation_rate = 0.2
        population_size = 50
        n_generations = 50

    costs, times, dists = [], [], []
    best_obj = None
    t_start = time.time()

    for seed in range(n_trials):
        if time.time() - t_start >= max_seconds:
            break
        np.random.seed(seed * 42 + 7)
        import random
        random.seed(seed * 42 + 7)
        t0 = time.time()
        ga = GeneticAlgorithm(
            data_dict,
            population_size=population_size,
            n_generations=n_generations,
            mutation_rate=mutation_rate,
            implement_local_search=False
        )
        ga.evolve()
        t1 = time.time() - t0
        costs.append(ga.best_path_len_downtime)
        times.append(t1)
        dists.append(ga.best_path_length)
        if best_obj is None or ga.best_path_len_downtime < best_obj["cost"]:
            best_obj = {
                "cost": ga.best_path_len_downtime,
                "distance": ga.best_path_length,
                "downtime": ga.best_downtime_days,
                "time_sec": t1,
                "tour": ga.best_path,
                "turbine_order": ga.turbine_order
            }

    return {
        "best_cost": float(min(costs)),
        "mean_cost": float(np.mean(costs)),
        "std_cost": float(np.std(costs)),
        "best_time": float(min(times)),
        "mean_time": float(np.mean(times)),
        "best_dist": float(min(dists)),
        "best_obj": best_obj
    }


def run_memetic_trials(data_dict: dict, n_turbines: int, max_seconds: int = TIMEOUT_PER_PROBLEM_SEC, n_trials: int = 5):
    if n_turbines >= 100:
        mutation_rate = 0.1
        population_size = 60
        n_generations = 20
    elif n_turbines >= 40:
        mutation_rate = 0.1
        population_size = 80
        n_generations = 30
    else:
        mutation_rate = 0.2
        population_size = 50
        n_generations = 10

    costs, times, dists = [], [], []
    best_obj = None
    t_start = time.time()

    for seed in range(n_trials):
        if time.time() - t_start >= max_seconds:
            break
        np.random.seed(seed * 42 + 7)
        import random
        random.seed(seed * 42 + 7)
        t0 = time.time()
        ga = GeneticAlgorithm(
            data_dict,
            population_size=population_size,
            n_generations=n_generations,
            mutation_rate=mutation_rate,
            implement_local_search=True
        )
        ga.evolve()
        t1 = time.time() - t0
        costs.append(ga.best_path_len_downtime)
        times.append(t1)
        dists.append(ga.best_path_length)
        if best_obj is None or ga.best_path_len_downtime < best_obj["cost"]:
            best_obj = {
                "cost": ga.best_path_len_downtime,
                "distance": ga.best_path_length,
                "downtime": ga.best_downtime_days,
                "time_sec": t1,
                "tour": ga.best_path,
                "turbine_order": ga.turbine_order
            }

    return {
        "best_cost": float(min(costs)),
        "mean_cost": float(np.mean(costs)),
        "std_cost": float(np.std(costs)),
        "best_time": float(min(times)),
        "mean_time": float(np.mean(times)),
        "best_dist": float(min(dists)),
        "best_obj": best_obj
    }


def main():
    print("=" * 80)
    print(f"BENCHMARK: COIN-OR CBC SOLVER VS HEURISTICS (TIMEOUT = {TIMEOUT_PER_PROBLEM_SEC}s / 5 min)")
    print("=" * 80)

    comparison_records = []

    for name, file_path, n_turbines in PROBLEMS:
        print(f"\n>>> Running: {name} (N = {n_turbines} turbines + 1 depot)")
        df, pts, dts, names, data_dict = load_problem_data(file_path)

        # 1. CBC Exact Solver
        print("  [1/4] Solving with Coin-OR CBC (MILP)...")
        cbc_res = solve_cbc(pts, dts, names, max_seconds=TIMEOUT_PER_PROBLEM_SEC)
        print(f"        -> Status: {cbc_res['status']}, Cost: {cbc_res['cost']:.6f}, Distance: {cbc_res['distance']:.6f}, DT: {cbc_res['downtime']:.6f}, Time: {cbc_res['time_sec']:.4f}s")

        # 2. Ant Colony Optimization (ACO)
        print("  [2/4] Solving with Ant Colony Optimization (ACO)...")
        aco_res = run_aco_trials(data_dict, n_turbines, max_seconds=TIMEOUT_PER_PROBLEM_SEC, n_trials=5)
        aco_gap = ((aco_res['best_cost'] - cbc_res['cost']) / cbc_res['cost']) * 100.0 if not np.isnan(cbc_res['cost']) else 0.0
        print(f"        -> Best Cost: {aco_res['best_cost']:.6f}, Gap: {aco_gap:.2f}%, Mean Time: {aco_res['mean_time']:.4f}s")

        # 3. Genetic Algorithm (GA)
        print("  [3/4] Solving with Genetic Algorithm (GA)...")
        ga_res = run_ga_trials(data_dict, n_turbines, max_seconds=TIMEOUT_PER_PROBLEM_SEC, n_trials=5)
        ga_gap = ((ga_res['best_cost'] - cbc_res['cost']) / cbc_res['cost']) * 100.0 if not np.isnan(cbc_res['cost']) else 0.0
        print(f"        -> Best Cost: {ga_res['best_cost']:.6f}, Gap: {ga_gap:.2f}%, Mean Time: {ga_res['mean_time']:.4f}s")

        # 4. Memetic Algorithm (GA + 2-opt)
        print("  [4/4] Solving with Memetic Algorithm (GA + 2-opt)...")
        mem_res = run_memetic_trials(data_dict, n_turbines, max_seconds=TIMEOUT_PER_PROBLEM_SEC, n_trials=5)
        mem_gap = ((mem_res['best_cost'] - cbc_res['cost']) / cbc_res['cost']) * 100.0 if not np.isnan(cbc_res['cost']) else 0.0
        print(f"        -> Best Cost: {mem_res['best_cost']:.6f}, Gap: {mem_gap:.2f}%, Mean Time: {mem_res['mean_time']:.4f}s")

        rec = {
            "problem": name,
            "n_turbines": n_turbines,
            "total_nodes": n_turbines + 1,
            # CBC Exact Results
            "cbc_opt_cost": cbc_res["cost"],
            "cbc_distance": cbc_res["distance"],
            "cbc_downtime": cbc_res["downtime"],
            "cbc_time_sec": cbc_res["time_sec"],
            "cbc_iterations": cbc_res["iterations"],
            "cbc_tour": cbc_res["tour"],
            "cbc_turbine_order": cbc_res["turbine_order"],
            # ACO Results
            "aco_best_cost": aco_res["best_cost"],
            "aco_mean_cost": aco_res["mean_cost"],
            "aco_std_cost": aco_res["std_cost"],
            "aco_gap_pct": aco_gap,
            "aco_mean_time_sec": aco_res["mean_time"],
            "aco_best_dist": aco_res["best_dist"],
            # GA Results
            "ga_best_cost": ga_res["best_cost"],
            "ga_mean_cost": ga_res["mean_cost"],
            "ga_std_cost": ga_res["std_cost"],
            "ga_gap_pct": ga_gap,
            "ga_mean_time_sec": ga_res["mean_time"],
            "ga_best_dist": ga_res["best_dist"],
            # Memetic Results
            "mem_best_cost": mem_res["best_cost"],
            "mem_mean_cost": mem_res["mean_cost"],
            "mem_std_cost": mem_res["std_cost"],
            "mem_gap_pct": mem_gap,
            "mem_mean_time_sec": mem_res["mean_time"],
            "mem_best_dist": mem_res["best_dist"],
        }
        comparison_records.append(rec)

    output_dir = BASE_DIR / "tests" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save CSV summary
    df_out = pd.DataFrame(comparison_records)
    csv_path = output_dir / "cbc_comparison_results.csv"
    df_out.to_csv(csv_path, index=False)
    print(f"\n[+] Saved results to {csv_path}")

    # Save JSON summary
    json_path = output_dir / "cbc_comparison_summary.json"
    with open(json_path, "w") as f:
        json.dump(comparison_records, f, indent=2)
    print(f"[+] Saved summary JSON to {json_path}")

    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY TABLE")
    print("=" * 80)
    summary_table = df_out[[
        "problem", "n_turbines",
        "cbc_opt_cost", "cbc_time_sec",
        "aco_best_cost", "aco_gap_pct", "aco_mean_time_sec",
        "ga_best_cost", "ga_gap_pct", "ga_mean_time_sec",
        "mem_best_cost", "mem_gap_pct", "mem_mean_time_sec"
    ]]
    print(summary_table.to_string(index=False))


if __name__ == "__main__":
    main()
