import pandas as pd
import itertools
import time as tm
import numpy as np
import asyncio
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))
sys.path.insert(0, str(BASE_DIR))
from scripts.genetic_algorithm import GeneticAlgorithm

class GeneticAlgorithmTests:
    def __init__(self) -> None:
        pass

    def chunker(self, seq, size):
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))

    def get_tests_tubine_fault_dict(self):
        problem_data_dict = {
            1: str(BASE_DIR / 'tests' / 'inputs' / 'problem_100_turbines.csv'),
            2: str(BASE_DIR / 'tests' / 'inputs' / 'problem_40_turbines.csv'),
            3: str(BASE_DIR / 'tests' / 'inputs' / 'problem_20_turbines.csv'),
            4: str(BASE_DIR / 'tests' / 'inputs' / 'problem_15_turbines.csv'),
            5: str(BASE_DIR / 'tests' / 'inputs' / 'problem_10_turbines.csv'),
            6: str(BASE_DIR / 'tests' / 'inputs' / 'problem_5_turbines.csv')
        }
        return problem_data_dict
    
    def get_problem_data(self, problem_number: int):
        problem_number_path = self.get_tests_tubine_fault_dict().get(problem_number)
        turbine_faults_df = pd.read_csv(problem_number_path, index_col=0)
        turbine_faults_df[['latitude_norm', 'longitude_norm']] = turbine_faults_df[['latitude', 'longitude']].apply(lambda x: (x - x.min()) / (x.max() - x.min()) if (x.max() - x.min()) > 0 else 0.0)
        turbine_faults_dict = turbine_faults_df.reset_index(drop=True).to_dict('index')
        return turbine_faults_dict
    
    async def get_params_results(self, problem_number: int, mutation_rate: float, population_size: int, number_of_generations: int, implement_local_search: bool):
        points = self.get_problem_data(problem_number=problem_number)

        init_time = tm.time()
        ga = GeneticAlgorithm(
            turbine_fault_list=points, 
            population_size=population_size, 
            n_generations=number_of_generations, 
            mutation_rate=mutation_rate,
            implement_local_search=implement_local_search)
        ga.evolve()
        # ant_colony.plot_path()
        end_run_time = tm.time() - init_time

        genetic_algorithm_path_obj = {
            'problem_number': [problem_number],
            'turbine_order': [ga.turbine_order],
            'best_path': [ga.best_path],
            'best_path_length': [ga.best_path_length],
            'best_downtime_days': [ga.best_downtime_days],
            'best_path_len_downtime': [ga.best_path_len_downtime],
            'time_to_run_sec': [end_run_time],
            'mutation_rate': [mutation_rate], 
            'population_size': [population_size],
            'number_of_generations': [number_of_generations]
        }

        return genetic_algorithm_path_obj

    async def test_best_params(self, n_iterations: int, output_filename: str, algorithm: str):

        for iter in range(n_iterations):
            for problem_number in range(1, 7):
                turbine_faults_dict = self.get_problem_data(problem_number)
                n_turbines = len(turbine_faults_dict) - 1
                start_run_time = tm.time()

                if algorithm == "Genetic":
                    implement_local_search = False
                    if n_turbines >= 15:
                        mutation_rate = 0.1
                        population_size = 100
                        n_generations = 50
                    else:
                        mutation_rate = 0.2
                        population_size = 50
                        n_generations = 50
                else:
                    implement_local_search = True
                    if n_turbines >= 40:
                        mutation_rate = 0.1
                        population_size = 150
                        n_generations = 50
                    else:
                        mutation_rate = 0.2
                        population_size = 50
                        n_generations = 10

                route_optimizer = GeneticAlgorithm(turbine_faults_dict, 
                                    population_size=population_size,
                                    n_generations=n_generations,
                                    mutation_rate=mutation_rate,
                                    implement_local_search=implement_local_search)
                route_optimizer.evolve()

                
                end_run_time = tm.time() - start_run_time
                turbine_order = route_optimizer.turbine_order

                # if turbine_order[0] == "Doca":
                #     turbine_order_to_show = [*turbine_order, *["Doca"]]
                # elif turbine_order[-1] == "Doca":
                #     turbine_order_to_show = [*["Doca"], *turbine_order]
                # else:
                #     turbine_order_to_show = [*turbine_order[turbine_order.index("Doca"):len(turbine_order) - 1], *turbine_order[:turbine_order.index("Doca")], *["Doca"]]

                route_optimzer_path_obj = {
                    'problem_number': [problem_number],
                    'turbine_order': [turbine_order],
                    'best_path': [route_optimizer.best_path],
                    'best_path_length': [route_optimizer.best_path_length],
                    'best_downtime_days': [route_optimizer.best_downtime_days],
                    'best_path_len_downtime': [route_optimizer.best_path_len_downtime],
                    'time_to_run_sec': [end_run_time],
                }
                print(route_optimzer_path_obj)
                
                pd.DataFrame(route_optimzer_path_obj).to_csv(output_filename, mode='a', header=False, index=False)



    async def run_grid_search(self, output_filename: str, implement_local_search: bool):
        # output_filename = r'tests\output\results_grid_search.csv'
        # Define three lists of hyperparameters
        mutation_rate_list = np.arange(0.1, 0.6, 0.1).round(2).astype(float).tolist()
        population_size_list = np.arange(50, 201, 50).astype(int).tolist()
        number_of_generations_list = np.arange(10, 51, 10).astype(int).tolist()

        # Create a list of all possible combinations of hyperparameters
        all_param_combinations = list(itertools.product(mutation_rate_list, population_size_list, number_of_generations_list))

        final_grid_search_results = pd.DataFrame(
            columns=['problem_number', 'turbine_order', 
                    'best_path', 'best_path_length', 
                    'best_downtime_days', 'best_path_len_downtime', 
                    'time_to_run_sec', 'mutation_rate', 'population_size'
                    'number_of_generations', 'tuple_params'])
        
        if not os.path.isfile(output_filename):
            # final_grid_search_results.to_csv(output_filename, index=False)
            pass
        else:
            final_grid_search_results = pd.read_csv(output_filename)
            final_grid_search_results['tuple_params'] = list(map(tuple, final_grid_search_results[['mutation_rate_list']].values))
        
        n_problems = 6
        n_iterations = 3
        for iter in range(n_iterations):
        # Perform grid search by iterating over all combinations
            for params in all_param_combinations:
                mutation_rate, population_size, number_of_generations = params

                if final_grid_search_results.loc[final_grid_search_results['tuple_params'] == params].shape[0] >= n_problems*n_iterations:
                    continue

                print(mutation_rate, population_size, number_of_generations)
                tasks = [self.get_params_results(
                            problem_number=problem_number, 
                            mutation_rate=mutation_rate, 
                            population_size=population_size, 
                            number_of_generations=number_of_generations,
                            implement_local_search=implement_local_search) for problem_number in range(1, 7)]
                results = await asyncio.gather(*tasks)

                genetic_algorithm_df = pd.concat([pd.DataFrame(genetic_algorithm_obj) for genetic_algorithm_obj in results]).reset_index(drop=True)
                genetic_algorithm_df['tuple_params'] = list(map(tuple, genetic_algorithm_df[['mutation_rate', 'population_size', 'number_of_generations']].values))


                pd.DataFrame(genetic_algorithm_df).to_csv(output_filename, mode='a', header=False, index=False)


if __name__ == "__main__":

    genetic_algorithm_tests = GeneticAlgorithmTests()
    # asyncio.run(genetic_algorithm_tests.run_grid_search(output_filename=r'tests\output\memetic_algo_results_grid_search_with_100_turbines_problems.csv', implement_local_search=True))
    asyncio.run(genetic_algorithm_tests.test_best_params(10, output_filename=r'tests\output\memetic_best_params_mean.csv', algorithm="Memetic"))

