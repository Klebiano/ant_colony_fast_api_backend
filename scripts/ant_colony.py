import numpy as np
import matplotlib.pyplot as plt
from typing import List
import time as tm


class AntColony():

    def __init__(self, turbine_fault_list: List[dict], n_ants: int, n_iterations: int, alpha: float, beta: float, evaporation_rate: float, Q: float) -> None:
        self.turbine_fault_list = turbine_fault_list
        self.n_ants = n_ants
        self.n_iterations = n_iterations
        self.n_points = len(self.turbine_fault_list.keys())
        self.pheromone = np.ones((self.n_points, self.n_points))
        self.best_path = None
        self.turbine_order = []
        # self.paths = []
        self.best_path_length = np.inf
        self.best_downtime_days = np.inf
        self.best_path_len_downtime = np.inf
        self.alpha = alpha
        self.beta = beta
        self.evaporation_rate = evaporation_rate
        self.Q = Q

    def distance(self, point_1: float, point_2: float) -> float:
        return np.sqrt(np.sum((point_1 - point_2)**2))

    def downtime_cost(self, fault_downtime_days_1, fault_downtime_days_2):
        return fault_downtime_days_1 + fault_downtime_days_2

    def objective_function(self, path):
        total_distance = 0
        total_downtime_cost = 0

        for i in range(len(path) - 1):
            total_distance += self.distance(np.array([self.turbine_fault_list[path[i]].get('latitude_norm'), self.turbine_fault_list[path[i]].get('longitude_norm')]), 
                                            np.array([self.turbine_fault_list[path[i + 1]].get('latitude_norm'), self.turbine_fault_list[path[i + 1]].get('longitude_norm')]))
            
            total_downtime_cost += self.downtime_cost(self.turbine_fault_list[path[i]].get('fault_downtime_days_norm'), 
                                                      self.turbine_fault_list[path[i + 1]].get('fault_downtime_days_norm'))

        return total_distance, total_downtime_cost

    def update_pheromone(self, objectives):

        for i in range(len(self.pheromone)):
            for j in range(len(self.pheromone)):
                delta_pheromone = 0
                for k in range(self.n_ants):
                    # if (objectives[k][0] <= objectives[i][0]) and (objectives[k][1] <= objectives[i][1]):
                    delta_pheromone += (self.Q / objectives[k][0]) + (self.Q / objectives[k][1])
                self.pheromone[i][j] = (1 - self.evaporation_rate) * self.pheromone[i][j] + delta_pheromone

    def ant_colony_optimization(self):

        for iteration in range(self.n_iterations):
            # paths = []
            # path_lengths = []
            objectives = []  # Store both distance and fuel cost objectives

            for ant in range(self.n_ants):
                # visited = [False] * self.n_points
                visited = {index: False for index in self.turbine_fault_list.keys()}
                # Start on the Docks 
                current_point = np.random.randint(self.n_points)
                # current_point = 0
                visited[current_point] = True
                path = [current_point]
                # path_length = 0

                while False in visited.values():
                    unvisited = {key: value for key, value in visited.items() if value == False}
                    probabilities = np.zeros(len(unvisited.keys()))

                    for i, unvisited_point in enumerate(unvisited.keys()):
                        pheromone_alpha = self.pheromone[current_point, unvisited_point] ** self.alpha
                        distance_beta = self.distance(np.array([self.turbine_fault_list[current_point].get('latitude_norm'), self.turbine_fault_list[current_point].get('longitude_norm')]), 
                                                      np.array([self.turbine_fault_list[unvisited_point].get('latitude_norm'), self.turbine_fault_list[unvisited_point].get('longitude_norm')])) ** self.beta
                        distance_beta += self.downtime_cost(self.turbine_fault_list[current_point].get('fault_downtime_days_norm'),
                                                            self.turbine_fault_list[unvisited_point].get('fault_downtime_days_norm')) ** self.beta
                        probabilities[i] = (pheromone_alpha / distance_beta)

                    probabilities /= np.sum(probabilities)

                    next_point = np.random.choice(list(unvisited.keys()), p=probabilities)
                    path.append(next_point)
                    visited[next_point] = True
                    current_point = next_point

                # Return to start
                path.append(path[0])

                # paths.append(path)
                # path_lengths.append(path_length)
                total_distance, total_downtime_cost = self.objective_function(path)
                objectives.append((total_distance, total_downtime_cost))
                # print(total_distance, total_downtime_cost, [self.turbine_fault_list[idx].get('turbine_name') for idx in path])

                if (total_distance + total_downtime_cost) < self.best_path_len_downtime:
                    self.best_path = path
                    self.turbine_order = [self.turbine_fault_list[idx].get('turbine_name') for i, idx in enumerate(path)]
                    self.best_path_length = total_distance
                    self.best_downtime_days = total_downtime_cost
                    self.best_path_len_downtime = total_distance + total_downtime_cost

            self.update_pheromone(objectives)

    def plot_path(self):
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111)  # , projection='3d')
        ax.scatter([data.get('latitude') for data in self.turbine_fault_list.values()], 
                   [data.get('longitude') for data in self.turbine_fault_list.values()], marker='o')

        for i in range(self.n_points - 1):

            current_item_best_path = self.best_path[i]
            next_item_best_path = self.best_path[i + 1]

            current_item_latitude = self.turbine_fault_list[current_item_best_path].get('latitude_norm')
            next_item_latitude = self.turbine_fault_list[next_item_best_path].get('latitude_norm')
            current_item_longitude = self.turbine_fault_list[current_item_best_path].get('longitude_norm')
            next_item_longitude = self.turbine_fault_list[next_item_best_path].get('longitude_norm')

            ax.plot([current_item_latitude, next_item_latitude],
                    [current_item_longitude, next_item_longitude],
                    c='g', linestyle='-', linewidth=2, marker='o')

        ax.plot([self.turbine_fault_list[self.best_path[0]].get('latitude_norm'), self.turbine_fault_list[self.best_path[-1]].get('latitude_norm')],
                [self.turbine_fault_list[self.best_path[0]].get('longitude_norm'), self.turbine_fault_list[self.best_path[-1]].get('longitude_norm')],
                c='r', linestyle='-', linewidth=2, marker='o')

        ax.set_xlabel('X Label')
        ax.set_ylabel('Y Label')
        # ax.set_zlabel('Z Label')
        plt.show()


if __name__ == "__main__":

    # Example usage:
    points = np.random.randn(20, 2)  # Generate 10 random 2D points
    ant_colony = AntColony(points, 
                           n_ants=20, 
                           n_iterations=100,
                           alpha=1, 
                           beta=2, 
                           evaporation_rate=0.5, 
                           Q=1)
    ant_colony.ant_colony_optimization()
    ant_colony.plot_path()

    ant_colony_path_obj = {
        'turbine_order': ant_colony.turbine_order,
        'best_path': ant_colony.best_path,
        'best_path_length': ant_colony.best_path_length,
        'best_downtime_days': ant_colony.best_downtime_days,
        'best_path_len_downtime': ant_colony.best_path_len_downtime,
        'time_to_run_sec': tm.time()
    }

    print(f"Best path: {ant_colony.best_path} | Best path length: {ant_colony.best_path_length} ")
