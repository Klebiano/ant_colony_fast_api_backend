import numpy as np
import matplotlib.pyplot as plt
from typing import List


class AntColony():

    def __init__(self, points: List[dict], n_ants: int, n_iterations: int, alpha: float, beta: float, evaporation_rate: float, Q: float) -> None:
        self.points = points
        self.n_ants = n_ants
        self.n_iterations = n_iterations
        self.n_points = len(self.points)
        self.pheromone = np.ones((self.n_points, self.n_points))
        self.best_path = None
        self.best_path_length = np.inf
        self.alpha = alpha
        self.beta = beta
        self.evaporation_rate = evaporation_rate
        self.Q = Q

    def distance(self, point_1: float, point_2: float) -> float:
        return np.sqrt(np.sum((point_1 - point_2)**2))

    def fuel_cost(self, point_1, point_2):
        fuel_efficiency = 0.1  # Adjust this value as needed
        fuel_price = 2.0      # Adjust this value as needed
        return 1

    def objective_function(self, path):
        total_distance = 0
        total_fuel_cost = 0

        for i in range(len(path) - 1):
            total_distance += self.distance(self.points[path[i]],
                                            self.points[path[i + 1]])
            total_fuel_cost += self.fuel_cost(
                self.points[path[i]], self.points[path[i + 1]])

        return total_distance, total_fuel_cost

    def update_pheromone(self, objectives):

        for i in range(len(self.pheromone)):
            for j in range(len(self.pheromone)):
                delta_pheromone = 0
                for k in range(self.n_ants):
                    if objectives[k][0] <= objectives[i][0] and objectives[k][1] <= objectives[i][1]:
                        delta_pheromone += self.Q / \
                            objectives[k][0] + self.Q / objectives[k][1]
                self.pheromone[i][j] = (
                    1 - self.evaporation_rate) * self.pheromone[i][j] + delta_pheromone

    def ant_colony_optimization(self):

        for iteration in range(self.n_iterations):
            paths = []
            path_lengths = []
            objectives = []  # Store both distance and fuel cost objectives

            for ant in range(self.n_ants):
                visited = [False] * self.n_points
                current_point = np.random.randint(self.n_points)
                visited[current_point] = True
                path = [current_point]
                path_length = 0

                while False in visited:
                    unvisited = np.where(np.logical_not(visited))[0]
                    probabilities = np.zeros(len(unvisited))

                    for i, unvisited_point in enumerate(unvisited):
                        probabilities[i] = self.pheromone[current_point, unvisited_point] * self.alpha / \
                            self.distance(
                                self.points[current_point], self.points[unvisited_point]) * self.beta

                    probabilities /= np.sum(probabilities)

                    next_point = np.random.choice(unvisited, p=probabilities)
                    path.append(next_point)
                    path_length += self.distance(
                        self.points[current_point], self.points[next_point])
                    visited[next_point] = True
                    current_point = next_point

                paths.append(path)
                path_lengths.append(path_length)
                total_distance, total_fuel_cost = self.objective_function(
                    path, points)
                objectives.append((total_distance, total_fuel_cost))

                if total_distance < self.best_path_length:
                    self.best_path = path
                    self.best_path_length = total_distance

            self.update_pheromone(objectives)

    def plot_path(self):
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111)  # , projection='3d')
        ax.scatter(self.points[:, 0], self.points[:, 1], c='r', marker='o')

        for i in range(self.n_points - 1):
            ax.plot([self.points[self.best_path[i], 0], self.points[self.best_path[i+1], 0]],
                    [self.points[self.best_path[i], 1],
                        self.points[self.best_path[i+1], 1]],
                    # [self.points[best_path[i],2], self.points[best_path[i+1],2]],
                    c='g', linestyle='-', linewidth=2, marker='o')

        ax.plot([self.points[self.best_path[0], 0], self.points[self.best_path[-1], 0]],
                [self.points[self.best_path[0], 1],
                    self.points[self.best_path[-1], 1]],
                # [points[best_path[0],2], points[best_path[-1],2]],
                c='g', linestyle='-', linewidth=2, marker='o')

        ax.set_xlabel('X Label')
        ax.set_ylabel('Y Label')
        # ax.set_zlabel('Z Label')
        plt.show()


if __name__ == "__main__":

    # Example usage:
    points = np.random.randn(20, 2)  # Generate 10 random 2D points
    ant_colony = AntColony(points, n_ants=20, n_iterations=100,
                           alpha=1, beta=1, evaporation_rate=0.5, Q=1)
    ant_colony.ant_colony_optimization()
    ant_colony.plot_path()

    print(
        f"Best path: {ant_colony.best_path} | Best path length: {ant_colony.best_path_length} ")
