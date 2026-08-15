import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Union, Any
import time as tm


class AntColony:

    def __init__(
        self,
        turbine_fault_list: Union[List[dict], Dict[Any, dict], np.ndarray],
        n_ants: int,
        n_iterations: int,
        alpha: float,
        beta: float,
        evaporation_rate: float,
        Q: float
    ) -> None:
        if isinstance(turbine_fault_list, dict):
            # Check if keys are 0..N-1
            if set(turbine_fault_list.keys()) == set(range(len(turbine_fault_list))):
                self.turbine_fault_list = dict(turbine_fault_list)
            else:
                self.turbine_fault_list = {i: v for i, v in enumerate(turbine_fault_list.values())}
        elif isinstance(turbine_fault_list, list):
            self.turbine_fault_list = {i: v for i, v in enumerate(turbine_fault_list)}
        elif isinstance(turbine_fault_list, np.ndarray):
            self.turbine_fault_list = {
                i: {
                    'latitude': pt[0],
                    'longitude': pt[1],
                    'latitude_norm': pt[0],
                    'longitude_norm': pt[1],
                    'fault_downtime_days': 0.0,
                    'fault_downtime_days_norm': 0.0,
                    'turbine_name': f'Point_{i}'
                }
                for i, pt in enumerate(turbine_fault_list)
            }
        else:
            self.turbine_fault_list = {i: v for i, v in enumerate(turbine_fault_list)}

        self.n_ants = n_ants
        self.n_iterations = n_iterations
        self.n_points = len(self.turbine_fault_list)
        self.pheromone = np.ones((self.n_points, self.n_points), dtype=float)
        self.best_path = None
        self.turbine_order = []
        self.best_path_length = np.inf
        self.best_downtime_days = np.inf
        self.best_path_len_downtime = np.inf
        self.alpha = alpha
        self.beta = beta
        self.evaporation_rate = evaporation_rate
        self.Q = Q

    def distance(self, point_1: np.ndarray, point_2: np.ndarray) -> float:
        return float(np.linalg.norm(point_1 - point_2))

    def downtime_cost(self, fault_downtime_days_1: float, fault_downtime_days_2: float) -> float:
        return float((fault_downtime_days_1 or 0.0) + (fault_downtime_days_2 or 0.0))

    def objective_function(self, path: List[int]) -> tuple:
        total_distance = 0.0
        total_downtime_cost = 0.0

        for i in range(len(path) - 1):
            p1 = self.turbine_fault_list[path[i]]
            p2 = self.turbine_fault_list[path[i + 1]]

            lat1 = p1.get('latitude_norm', p1.get('latitude', 0.0))
            lon1 = p1.get('longitude_norm', p1.get('longitude', 0.0))
            lat2 = p2.get('latitude_norm', p2.get('latitude', 0.0))
            lon2 = p2.get('longitude_norm', p2.get('longitude', 0.0))

            total_distance += self.distance(np.array([lat1, lon1]), np.array([lat2, lon2]))
            total_downtime_cost += self.downtime_cost(
                p1.get('fault_downtime_days_norm', p1.get('fault_downtime_days', 0.0)),
                p2.get('fault_downtime_days_norm', p2.get('fault_downtime_days', 0.0))
            )

        return total_distance, total_downtime_cost

    def update_pheromone(self, paths: List[List[int]], objectives: List[tuple]) -> None:
        # Pheromone evaporation on all edges
        self.pheromone = (1.0 - self.evaporation_rate) * self.pheromone

        # Deposit pheromone strictly on edges traversed by each ant
        for k in range(len(paths)):
            total_distance, total_downtime = objectives[k]
            total_cost = total_distance + total_downtime
            if total_cost > 1e-9:
                delta_pheromone = self.Q / total_cost
            else:
                delta_pheromone = self.Q

            path = paths[k]
            for t in range(len(path) - 1):
                u = path[t]
                v = path[t + 1]
                self.pheromone[u, v] += delta_pheromone
                self.pheromone[v, u] += delta_pheromone

        # Avoid pheromone vanishing to exact 0
        np.clip(self.pheromone, a_min=1e-6, a_max=None, out=self.pheromone)

    def ant_colony_optimization(self) -> None:
        if self.n_points == 0:
            self.best_path = []
            self.turbine_order = []
            self.best_path_length = 0.0
            self.best_downtime_days = 0.0
            self.best_path_len_downtime = 0.0
            return

        if self.n_points == 1:
            self.best_path = [0, 0]
            self.turbine_order = [self.turbine_fault_list[0].get('turbine_name', 'Point_0')] * 2
            total_dist, total_dt = self.objective_function(self.best_path)
            self.best_path_length = total_dist
            self.best_downtime_days = total_dt
            self.best_path_len_downtime = total_dist + total_dt
            return

        for iteration in range(self.n_iterations):
            paths = []
            objectives = []

            for ant in range(self.n_ants):
                visited = {index: False for index in range(self.n_points)}
                current_point = np.random.randint(self.n_points)
                visited[current_point] = True
                path = [current_point]

                while False in visited.values():
                    unvisited_keys = [k for k, v in visited.items() if not v]
                    probabilities = np.zeros(len(unvisited_keys), dtype=float)

                    curr_data = self.turbine_fault_list[current_point]
                    curr_lat = curr_data.get('latitude_norm', curr_data.get('latitude', 0.0))
                    curr_lon = curr_data.get('longitude_norm', curr_data.get('longitude', 0.0))
                    curr_dt = curr_data.get('fault_downtime_days_norm', curr_data.get('fault_downtime_days', 0.0))

                    for i, unvisited_point in enumerate(unvisited_keys):
                        target_data = self.turbine_fault_list[unvisited_point]
                        target_lat = target_data.get('latitude_norm', target_data.get('latitude', 0.0))
                        target_lon = target_data.get('longitude_norm', target_data.get('longitude', 0.0))
                        target_dt = target_data.get('fault_downtime_days_norm', target_data.get('fault_downtime_days', 0.0))

                        dist = self.distance(np.array([curr_lat, curr_lon]), np.array([target_lat, target_lon]))
                        dt = self.downtime_cost(curr_dt, target_dt)
                        combined_cost = dist + dt

                        pheromone_val = self.pheromone[current_point, unvisited_point] ** self.alpha
                        heuristic_val = (1.0 / (combined_cost + 1e-10)) ** self.beta

                        probabilities[i] = pheromone_val * heuristic_val

                    prob_sum = np.sum(probabilities)
                    if prob_sum > 0 and not np.isnan(prob_sum):
                        probabilities /= prob_sum
                    else:
                        probabilities = np.ones(len(unvisited_keys)) / len(unvisited_keys)

                    next_point = np.random.choice(unvisited_keys, p=probabilities)
                    path.append(next_point)
                    visited[next_point] = True
                    current_point = next_point

                # Complete closed TSP cycle back to start
                path.append(path[0])

                total_distance, total_downtime_cost = self.objective_function(path)
                total_cost = total_distance + total_downtime_cost
                paths.append(path)
                objectives.append((total_distance, total_downtime_cost))

                if total_cost < self.best_path_len_downtime:
                    self.best_path = path
                    self.turbine_order = [self.turbine_fault_list[idx].get('turbine_name', f'Turbine_{idx}') for idx in path]
                    self.best_path_length = total_distance
                    self.best_downtime_days = total_downtime_cost
                    self.best_path_len_downtime = total_cost

            self.update_pheromone(paths, objectives)

    def plot_path(self):
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111)

        latitudes = [data.get('latitude_norm', data.get('latitude', 0.0)) for data in self.turbine_fault_list.values()]
        longitudes = [data.get('longitude_norm', data.get('longitude', 0.0)) for data in self.turbine_fault_list.values()]
        ax.scatter(latitudes, longitudes, marker='o')

        if self.best_path and len(self.best_path) > 1:
            for i in range(len(self.best_path) - 1):
                curr_idx = self.best_path[i]
                next_idx = self.best_path[i + 1]

                c_lat = self.turbine_fault_list[curr_idx].get('latitude_norm', self.turbine_fault_list[curr_idx].get('latitude', 0.0))
                c_lon = self.turbine_fault_list[curr_idx].get('longitude_norm', self.turbine_fault_list[curr_idx].get('longitude', 0.0))
                n_lat = self.turbine_fault_list[next_idx].get('latitude_norm', self.turbine_fault_list[next_idx].get('latitude', 0.0))
                n_lon = self.turbine_fault_list[next_idx].get('longitude_norm', self.turbine_fault_list[next_idx].get('longitude', 0.0))

                ax.plot([c_lat, n_lat], [c_lon, n_lon], c='g', linestyle='-', linewidth=2, marker='o')

        ax.set_xlabel('Latitude (norm)')
        ax.set_ylabel('Longitude (norm)')
        plt.title('Ant Colony Optimization Best Path')
        plt.show()


if __name__ == "__main__":
    np.random.seed(42)
    sample_points = []
    for i in range(10):
        sample_points.append({
            'turbine_name': f'Turbine_{i}',
            'latitude': float(np.random.uniform(-10, 10)),
            'longitude': float(np.random.uniform(-10, 10)),
            'latitude_norm': float(np.random.uniform(0, 1)),
            'longitude_norm': float(np.random.uniform(0, 1)),
            'fault_downtime_days': float(np.random.uniform(0, 5)),
            'fault_downtime_days_norm': float(np.random.uniform(0, 1))
        })

    ant_colony = AntColony(
        turbine_fault_list=sample_points,
        n_ants=10,
        n_iterations=50,
        alpha=1.0,
        beta=2.0,
        evaporation_rate=0.5,
        Q=100.0
    )
    ant_colony.ant_colony_optimization()

    ant_colony_path_obj = {
        'turbine_order': ant_colony.turbine_order,
        'best_path': ant_colony.best_path,
        'best_path_length': ant_colony.best_path_length,
        'best_downtime_days': ant_colony.best_downtime_days,
        'best_path_len_downtime': ant_colony.best_path_len_downtime,
        'time_to_run_sec': tm.time()
    }

    print(f"Best path: {ant_colony.best_path}")
    print(f"Best path length: {ant_colony.best_path_length:.4f}")
    print(f"Best downtime: {ant_colony.best_downtime_days:.4f}")
    print(f"Best total cost: {ant_colony.best_path_len_downtime:.4f}")
    print(f"Turbine order: {ant_colony.turbine_order}")
