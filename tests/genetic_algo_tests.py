import pandas as pd
import itertools
import time as tm
import numpy as np
import asyncio
import sys
import os
sys.path.append(r"C:\Users\klebi\OneDrive\Documentos\TCC\offshore_ant_web_dev\backend\scripts")


class GeneticAlgorithmTests:
    def __init__(self) -> None:
        pass

    def chunker(self, seq, size):
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))

    def get_tests_tubine_fault_dict(self):
        problem_data_dict = {
            1: 'tests\\inputs\\problem_40_turbines.csv',
            2: 'tests\\inputs\\problem_20_turbines.csv',
            3: 'tests\\inputs\\problem_15_turbines.csv',
            4: 'tests\\inputs\\problem_10_turbines.csv',
            5: 'tests\\inputs\\problem_5_turbines.csv'
        }
        return problem_data_dict
    
    def get_problem_data(self, problem_number: int):
        problem_number_path = self.get_tests_tubine_fault_dict().get(problem_number)
        turbine_faults_df = pd.read_csv(problem_number_path, index_col=0)
        turbine_faults_df[['latitude_norm', 'longitude_norm']] = turbine_faults_df[['latitude', 'longitude']].apply(lambda x: (x - x.min()) / (x.max() - x.min()))
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

    async def test_best_params(self, n_iterations: int, output_filename: str):

        for iter in range(n_iterations):
            for problem_number in range(1, 6):
                turbine_faults_dict = self.get_problem_data(problem_number)

                n_turbines = len(turbine_faults_dict.keys()) - 1
                if n_turbines <= 10:
                    n_ants = 3
                    alpha = 5
                    beta = 1.5
                    rho = 0.5
                else:
                    n_ants = 8
                    alpha = 5
                    beta = 2
                    rho = 0.5

                start_run_time = tm.time()
                ant_colony = AntColony(turbine_faults_dict, 
                                    n_ants=n_ants, 
                                    n_iterations=200,
                                    alpha=alpha, 
                                    beta=beta, 
                                    evaporation_rate=rho, 
                                    Q=100)
                ant_colony.ant_colony_optimization()
                end_run_time = tm.time() - start_run_time
                
                ant_colony_path_obj = {
                    'problem_number': [problem_number],		
                    'turbine_order': [ant_colony.turbine_order],
                    'best_path': [ant_colony.best_path],
                    'best_path_length': [ant_colony.best_path_length],
                    'best_downtime_days': [ant_colony.best_downtime_days],
                    'best_path_len_downtime': [ant_colony.best_path_len_downtime],
                    'time_to_run_sec': [end_run_time],
                }
                print(ant_colony_path_obj)
                
                pd.DataFrame(ant_colony_path_obj).to_csv(output_filename, mode='a', header=False, index=False)



    async def run_grid_search(self, output_filename: str):
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
        
        n_problems = 5
        n_iterations = 5
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
                            implement_local_search=True) for problem_number in range(1, 6)]
                results = await asyncio.gather(*tasks)

                genetic_algorithm_df = pd.concat([pd.DataFrame(genetic_algorithm_obj) for genetic_algorithm_obj in results]).reset_index(drop=True)
                genetic_algorithm_df['tuple_params'] = list(map(tuple, genetic_algorithm_df[['mutation_rate', 'population_size', 'number_of_generations']].values))


                pd.DataFrame(genetic_algorithm_df).to_csv(output_filename, mode='a', header=False, index=False)


if __name__ == "__main__":

    from genetic_algorithm import GeneticAlgorithm

    genetic_algorithm_tests = GeneticAlgorithmTests()
    asyncio.run(genetic_algorithm_tests.run_grid_search(output_filename=r'tests\output\memetic_algo_results_grid_search.csv'))
    # asyncio.run(genetic_algorithm_tests.test_best_params(100, output_filename=r'tests\output\ga_best_params_mean.csv'))

