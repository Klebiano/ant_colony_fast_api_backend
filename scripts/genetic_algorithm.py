import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple
import random
import time as tm

class GeneticAlgorithm:
    def __init__(self, turbine_fault_list: List[dict], population_size: int, n_generations: int, mutation_rate: float, implement_local_search=False) -> None:
        self.turbine_fault_list = turbine_fault_list
        self.population_size = population_size
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
        return [random.sample(range(self.n_points), self.n_points) for _ in range(self.population_size)]

    def distance(self, point_1: np.ndarray, point_2: np.ndarray) -> float:
        return np.linalg.norm(point_1 - point_2)

    def downtime_cost(self, fault_downtime_days_1: float, fault_downtime_days_2: float) -> float:
        return fault_downtime_days_1 + fault_downtime_days_2
    
    def calculate_total_distance(self, route: List[int]) -> float:
        """
        Calcula a distância total percorrida para uma determinada rota.

        Args:
            route (List[int]): Lista representando a sequência de turbinas visitadas.

        Returns:
            float: Distância total da rota.
        """
        total_distance = 0.0
        for i in range(len(route) - 1):
            total_distance += self.distance(
                np.array([self.turbine_fault_list[route[i]]['latitude_norm'], 
                        self.turbine_fault_list[route[i]]['longitude_norm']]), 
                np.array([self.turbine_fault_list[route[i + 1]]['latitude_norm'], 
                        self.turbine_fault_list[route[i + 1]]['longitude_norm']])
            )
        
        # Adiciona a distância para retornar ao ponto inicial (rota fechada)
        total_distance += self.distance(
            np.array([self.turbine_fault_list[route[-1]]['latitude_norm'], 
                    self.turbine_fault_list[route[-1]]['longitude_norm']]), 
            np.array([self.turbine_fault_list[route[0]]['latitude_norm'], 
                    self.turbine_fault_list[route[0]]['longitude_norm']])
        )

        return total_distance


    def objective_function(self, path):
        total_distance = 0
        total_downtime_cost = 0

        for i in range(len(path) - 1):
            total_distance += self.distance(np.array([self.turbine_fault_list[path[i]].get('latitude_norm'), self.turbine_fault_list[path[i]].get('longitude_norm')]), 
                                            np.array([self.turbine_fault_list[path[i + 1]].get('latitude_norm'), self.turbine_fault_list[path[i + 1]].get('longitude_norm')]))
            
            total_downtime_cost += self.downtime_cost(self.turbine_fault_list[path[i]].get('fault_downtime_days_norm'), 
                                                      self.turbine_fault_list[path[i + 1]].get('fault_downtime_days_norm'))

        return total_distance, total_downtime_cost

    def selection(self) -> List[List[int]]:
        evaluated_population = [(ind, sum(self.objective_function(ind))) for ind in self.population]
        evaluated_population.sort(key=lambda x: x[1])
        return [ind for ind, obj in evaluated_population[:self.population_size // 2]]

    def crossover(self, parent1: List[int], parent2: List[int]) -> List[int]:
        start, end = sorted(random.sample(range(self.n_points), 2))
        child = [-1] * self.n_points
        child[start:end] = parent1[start:end]
        pointer = end % self.n_points
        for i in range(self.n_points):
            gene = parent2[(end + i) % self.n_points]
            if gene not in child:
                child[pointer] = gene
                pointer = (pointer + 1) % self.n_points
        return child

    def mutate(self, individual: List[int]) -> List[int]:
        if random.random() < self.mutation_rate:
            i, j = random.sample(range(self.n_points), 2)
            individual[i], individual[j] = individual[j], individual[i]
        return individual

    def two_opt(self, route: List[int], max_iterations: int = 10) -> List[int]:
        best = route
        count = 0
        while count < max_iterations:
            improved = False
            for i in range(1, len(route) - 2):
                for j in range(i + 1, len(route)):
                    if j - i == 1:
                        continue
                    new_route = route[:]
                    new_route[i:j] = route[j - 1:i - 1:-1]
                    if self.calculate_total_distance(new_route) < self.calculate_total_distance(best):
                        best = new_route
                        improved = True
                        break  # Saia do loop interno
                if improved:
                    break  # Saia do loop externo
            if not improved:
                break
            route = best
            count += 1
        return best

    def evolve(self) -> None:
        for generation in range(self.n_generations):
            new_population = []
            selected_individuals = self.selection()
            while len(new_population) < self.population_size:
                parent1, parent2 = random.sample(selected_individuals, 2)
                child = self.crossover(parent1, parent2)
                child = self.mutate(child)
                if self.implement_local_search:
                   # Aplicar busca local apenas a alguns indivíduos
                    if random.random() < 0.2:
                        child = self.two_opt(child)
                new_population.append(child)
            self.population = new_population

            # Avaliação da nova população
            for individual in self.population:
                individual = individual + [individual[0]]  # Retorna ao ponto inicial
                total_distance, total_downtime_cost = self.objective_function(individual)
                if (total_distance + total_downtime_cost) < self.best_path_len_downtime:
                    self.best_path = individual
                    self.best_path_length = total_distance
                    self.best_downtime_days = total_downtime_cost
                    self.best_path_len_downtime = total_distance + total_downtime_cost
                    self.turbine_order = [self.turbine_fault_list[idx]['turbine_name'] for idx in self.best_path]

    def plot_path(self):
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        latitudes = [data['latitude'] for data in self.turbine_fault_list]
        longitudes = [data['longitude'] for data in self.turbine_fault_list]
        ax.scatter(latitudes, longitudes, marker='o')
        for i in range(len(self.best_path) - 1):
            current_idx = self.best_path[i]
            next_idx = self.best_path[i + 1]
            current_latitude = self.turbine_fault_list[current_idx]['latitude']
            next_latitude = self.turbine_fault_list[next_idx]['latitude']
            current_longitude = self.turbine_fault_list[current_idx]['longitude']
            next_longitude = self.turbine_fault_list[next_idx]['longitude']
            ax.plot([current_latitude, next_latitude],
                    [current_longitude, next_longitude],
                    c='g', linestyle='-', linewidth=2, marker='o')
        ax.set_xlabel('Latitude')
        ax.set_ylabel('Longitude')
        plt.title('Melhor Rota Encontrada (Algoritmo Memético)')
        plt.show()

if __name__ == "__main__":
    # Mesmos dados de exemplo do código anterior
    import random

    num_turbines = 20
    turbine_fault_list = []
    for i in range(num_turbines):
        turbine = {
            'turbine_name': f'Turbine_{i}',
            'latitude': random.uniform(-10, 10),
            'longitude': random.uniform(-10, 10),
            'fault_downtime_days': random.uniform(1, 5)
        }
        turbine_fault_list.append(turbine)

    # Normalização dos dados
    latitudes = [t['latitude'] for t in turbine_fault_list]
    longitudes = [t['longitude'] for t in turbine_fault_list]
    downtimes = [t['fault_downtime_days'] for t in turbine_fault_list]

    max_latitude = max(latitudes)
    min_latitude = min(latitudes)
    max_longitude = max(longitudes)
    min_longitude = min(longitudes)
    max_downtime = max(downtimes)
    min_downtime = min(downtimes)

    for t in turbine_fault_list:
        t['latitude_norm'] = (t['latitude'] - min_latitude) / (max_latitude - min_latitude)
        t['longitude_norm'] = (t['longitude'] - min_longitude) / (max_longitude - min_longitude)
        t['fault_downtime_days_norm'] = (t['fault_downtime_days'] - min_downtime) / (max_downtime - min_downtime)

    ga = GeneticAlgorithm(turbine_fault_list=turbine_fault_list,
                          population_size=50,
                          n_generations=200,
                          mutation_rate=0.1)
    ga.evolve()
    ga.plot_path()

    ga_path_obj = {
        'best_path': ga.best_path,
        'best_path_length': ga.best_path_length,
        'best_downtime_days': ga.best_downtime_days,
        'best_path_len_downtime': ga.best_path_len_downtime,
        'turbine_order': ga.turbine_order,
        'time_to_run_sec': tm.time()
    }

    print(f"Melhor caminho: {ga.best_path}")
    print(f"Comprimento do melhor caminho: {ga.best_path_length}")
    print(f"Custo total de downtime: {ga.best_downtime_days}")
    print(f"Soma total (distância + downtime): {ga.best_path_len_downtime}")
    print(f"Ordem das turbinas visitadas: {ga.turbine_order}")
