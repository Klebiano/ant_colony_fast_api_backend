import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Union, Any
import random
import time as tm


class GeneticAlgorithm:

    def __init__(
        self,
        turbine_fault_list: Union[List[dict], Dict[Any, dict], np.ndarray],
        population_size: int,
        n_generations: int,
        mutation_rate: float,
        implement_local_search: bool = False
    ) -> None:
        if isinstance(turbine_fault_list, dict):
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

        self.population_size = max(4, population_size)
        self.n_generations = n_generations
        self.n_points = len(self.turbine_fault_list)
        self.mutation_rate = mutation_rate
        self.implement_local_search = implement_local_search
        self.population = self.initialize_population()
        self.turbine_order = []
        self.best_path = None
        self.best_path_length = np.inf
        self.best_downtime_days = np.inf
        self.best_path_len_downtime = np.inf

    def initialize_population(self) -> List[List[int]]:
        if self.n_points == 0:
            return []
        if self.n_points == 1:
            return [[0] for _ in range(self.population_size)]
        return [random.sample(range(self.n_points), self.n_points) for _ in range(self.population_size)]

    def distance(self, point_1: np.ndarray, point_2: np.ndarray) -> float:
        return float(np.linalg.norm(point_1 - point_2))

    def downtime_cost(self, fault_downtime_days_1: float, fault_downtime_days_2: float) -> float:
        return float((fault_downtime_days_1 or 0.0) + (fault_downtime_days_2 or 0.0))

    def calculate_total_distance(self, route: List[int]) -> float:
        total_distance, _ = self.objective_function(route)
        return total_distance

    def objective_function(self, path: List[int]) -> tuple:
        if not path or len(path) <= 1:
            return 0.0, 0.0

        # If path is an unclosed permutation of length N, add return step to path[0]
        if len(path) == self.n_points and self.n_points > 1 and path[0] != path[-1]:
            full_path = path + [path[0]]
        else:
            full_path = path

        total_distance = 0.0
        total_downtime_cost = 0.0

        for i in range(len(full_path) - 1):
            p1 = self.turbine_fault_list[full_path[i]]
            p2 = self.turbine_fault_list[full_path[i + 1]]

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

    def selection(self) -> List[List[int]]:
        evaluated_population = [(ind, sum(self.objective_function(ind))) for ind in self.population]
        evaluated_population.sort(key=lambda x: x[1])
        num_selected = max(2, self.population_size // 2)
        return [ind for ind, _ in evaluated_population[:num_selected]]

    def crossover(self, parent1: List[int], parent2: List[int]) -> List[int]:
        if self.n_points <= 2:
            return parent1[:]

        start, end = sorted(random.sample(range(self.n_points), 2))
        child = [-1] * self.n_points
        child[start:end] = parent1[start:end]
        copied_genes = set(child[start:end])

        pointer = end % self.n_points
        for i in range(self.n_points):
            gene = parent2[(end + i) % self.n_points]
            if gene not in copied_genes:
                child[pointer] = gene
                copied_genes.add(gene)
                pointer = (pointer + 1) % self.n_points

        return child

    def mutate(self, individual: List[int]) -> List[int]:
        if self.n_points >= 2 and random.random() < self.mutation_rate:
            i, j = random.sample(range(self.n_points), 2)
            individual[i], individual[j] = individual[j], individual[i]
        return individual

    def two_opt(self, route: List[int], max_iterations: int = 10) -> List[int]:
        if self.n_points < 4:
            return route

        best = list(route)
        best_cost = sum(self.objective_function(best))
        count = 0

        while count < max_iterations:
            improved = False
            for i in range(0, self.n_points - 1):
                for j in range(i + 1, self.n_points):
                    if i == 0 and j == self.n_points - 1:
                        continue
                    new_route = best[:i] + best[i:j + 1][::-1] + best[j + 1:]
                    new_cost = sum(self.objective_function(new_route))
                    if new_cost < best_cost - 1e-9:
                        best = new_route
                        best_cost = new_cost
                        improved = True
                        break
                if improved:
                    break
            if not improved:
                break
            count += 1
        return best

    def evolve(self) -> None:
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

        # Initial evaluation
        for individual in self.population:
            closed_path = [int(x) for x in individual] + [int(individual[0])]
            total_distance, total_downtime_cost = self.objective_function(closed_path)
            total_cost = total_distance + total_downtime_cost
            if total_cost < self.best_path_len_downtime:
                self.best_path = closed_path
                self.best_path_length = total_distance
                self.best_downtime_days = total_downtime_cost
                self.best_path_len_downtime = total_cost
                self.turbine_order = [self.turbine_fault_list[idx].get('turbine_name', f'Turbine_{idx}') for idx in self.best_path]

        for generation in range(self.n_generations):
            selected_individuals = self.selection()
            # Elitism: preserve top 2 individuals
            new_population = [ind[:] for ind in selected_individuals[:2]]

            while len(new_population) < self.population_size:
                parent1, parent2 = random.sample(selected_individuals, 2)
                child = self.crossover(parent1, parent2)
                child = self.mutate(child)
                if self.implement_local_search and random.random() < 0.2:
                    child = self.two_opt(child)
                new_population.append(child)

            self.population = new_population

            # Evaluation of the new population
            for individual in self.population:
                closed_path = [int(x) for x in individual] + [int(individual[0])]
                total_distance, total_downtime_cost = self.objective_function(closed_path)
                total_cost = total_distance + total_downtime_cost
                if total_cost < self.best_path_len_downtime:
                    self.best_path = closed_path
                    self.best_path_length = total_distance
                    self.best_downtime_days = total_downtime_cost
                    self.best_path_len_downtime = total_cost
                    self.turbine_order = [self.turbine_fault_list[idx].get('turbine_name', f'Turbine_{idx}') for idx in self.best_path]

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

        ax.set_xlabel('Latitude')
        ax.set_ylabel('Longitude')
        title_suffix = 'Memético' if self.implement_local_search else 'Genético'
        plt.title(f'Melhor Rota Encontrada (Algoritmo {title_suffix})')
        plt.show()


if __name__ == "__main__":
    random.seed(42)
    np.random.seed(42)

    num_turbines = 20
    sample_turbines = []
    for i in range(num_turbines):
        sample_turbines.append({
            'turbine_name': f'Turbine_{i}',
            'latitude': random.uniform(-10, 10),
            'longitude': random.uniform(-10, 10),
            'fault_downtime_days': random.uniform(1, 5)
        })

    latitudes = [t['latitude'] for t in sample_turbines]
    longitudes = [t['longitude'] for t in sample_turbines]
    downtimes = [t['fault_downtime_days'] for t in sample_turbines]

    max_lat, min_lat = max(latitudes), min(latitudes)
    max_lon, min_lon = max(longitudes), min(longitudes)
    max_dt, min_dt = max(downtimes), min(downtimes)

    for t in sample_turbines:
        t['latitude_norm'] = (t['latitude'] - min_lat) / (max_lat - min_lat) if max_lat > min_lat else 0.0
        t['longitude_norm'] = (t['longitude'] - min_lon) / (max_lon - min_lon) if max_lon > min_lon else 0.0
        t['fault_downtime_days_norm'] = (t['fault_downtime_days'] - min_dt) / (max_dt - min_dt) if max_dt > min_dt else 0.0

    ga = GeneticAlgorithm(
        turbine_fault_list=sample_turbines,
        population_size=50,
        n_generations=100,
        mutation_rate=0.1,
        implement_local_search=True
    )
    ga.evolve()

    ga_path_obj = {
        'best_path': ga.best_path,
        'best_path_length': ga.best_path_length,
        'best_downtime_days': ga.best_downtime_days,
        'best_path_len_downtime': ga.best_path_len_downtime,
        'turbine_order': ga.turbine_order,
        'time_to_run_sec': tm.time()
    }

    print(f"Melhor caminho: {ga.best_path}")
    print(f"Comprimento do melhor caminho: {ga.best_path_length:.4f}")
    print(f"Custo total de downtime: {ga.best_downtime_days:.4f}")
    print(f"Soma total (distância + downtime): {ga.best_path_len_downtime:.4f}")
    print(f"Ordem das turbinas visitadas: {ga.turbine_order}")
