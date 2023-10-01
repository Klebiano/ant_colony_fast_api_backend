import pandas as pd
import itertools
import time as tm
import numpy as np
import asyncio
import sys
sys.path.append(r"C:\Users\klebi\OneDrive\Documentos\TCC\offshore_ant_web_dev\backend\scripts")

class AntColonyTests:
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
        
    def get_glpk_tables(self, problem_number: int):
        problem_number_path = self.get_tests_tubine_fault_dict().get(problem_number)
        turbine_faults_df = pd.read_csv(problem_number_path, index_col=0).reset_index(drop=True)
        turbine_faults_df[['latitude_norm', 'longitude_norm']] = turbine_faults_df[['latitude', 'longitude']].apply(lambda x: (x - x.min()) / (x.max() - x.min()))        
        turbine_faults_df.index = turbine_faults_df.index + 1
        
        turbine_faults_dict = turbine_faults_df.reset_index(drop=True)

        ant_colony = AntColony(turbine_faults_dict, 
                                n_ants=None, 
                                n_iterations=0,
                                alpha=0, 
                                beta=0, 
                                evaporation_rate=0, 
                                Q=0)

        sym_distance_matrix = pd.DataFrame(index=turbine_faults_df.index, columns=turbine_faults_df.index)
        sym_time_matrix = pd.DataFrame(index=turbine_faults_df.index, columns=turbine_faults_df.index)
        for i, i_row in enumerate(turbine_faults_df.itertuples()):
            for j, j_row in enumerate(turbine_faults_df.itertuples()):
                sym_distance_matrix[i + 1][j + 1] = ant_colony.distance(np.array([i_row.latitude_norm, i_row.longitude_norm]), 
                                                                np.array([j_row.latitude_norm, j_row.longitude_norm])) if not i == j else 0

                sym_time_matrix[i + 1][j + 1] = ant_colony.downtime_cost(i_row.fault_downtime_days_norm, j_row.fault_downtime_days_norm) if not i == j else 0

        return
    
    
    async def get_params_results(self, problem_number: int, n_ants: int, alpha: int, beta: int, rho: int):
        points = self.get_problem_data(problem_number=problem_number)

        init_time = tm.time()
        ant_colony = AntColony(points, 
                            n_ants=n_ants, 
                            n_iterations=100,
                            alpha=alpha, 
                            beta=beta, 
                            evaporation_rate=rho, 
                            Q=100)
        ant_colony.ant_colony_optimization()
        # ant_colony.plot_path()
        end_run_time = tm.time() - init_time

        ant_colony_path_obj = {
            'problem_number': [problem_number],
            'turbine_order': [ant_colony.turbine_order],
            'best_path': [ant_colony.best_path],
            'best_path_length': [ant_colony.best_path_length],
            'best_downtime_days': [ant_colony.best_downtime_days],
            'best_path_len_downtime': [ant_colony.best_path_len_downtime],
            'time_to_run_sec': [end_run_time],
            'n_ants': [n_ants], 
            'alpha': [alpha], 
            'beta': [beta], 
            'rho': [rho]
        }

        return ant_colony_path_obj


    async def run_grid_search(self, output_filename: str):
        # output_filename = r'tests\output\results_grid_search.csv'
        # Define three lists of hyperparameters
        ant_number_list = np.linspace(1, 10, 5).astype(int).tolist()
        alpha_number_list = np.linspace(1, 10, 5).astype(int).tolist()
        beta_number_list = np.linspace(0, 2, 3).tolist()
        rho_number_list = np.linspace(0, 1, 3).tolist()

        # Create a list of all possible combinations of hyperparameters
        all_param_combinations = list(itertools.product(ant_number_list, alpha_number_list, beta_number_list, rho_number_list))

        final_grid_search_results = pd.DataFrame(
            columns=['problem_number', 'turbine_order', 
                    'best_path', 'best_path_length', 
                    'best_downtime_days', 'best_path_len_downtime', 
                    'time_to_run_sec'])
        final_grid_search_results.to_csv(output_filename, index=False)
        
        for iter in range(20):
        # Perform grid search by iterating over all combinations
            for params in all_param_combinations:
                n_ants, alpha, beta, rho = params

                print(n_ants, alpha, beta, rho)
                tasks = [self.get_params_results(problem_number=problem_number, n_ants=n_ants, alpha=alpha, beta=beta, rho=rho) for problem_number in range(1, 6)]
                results = await asyncio.gather(*tasks)

                ant_colony_path_df = pd.concat([pd.DataFrame(ant_colony_path_obj) for ant_colony_path_obj in results]).reset_index(drop=True)

                pd.DataFrame(ant_colony_path_df).to_csv(output_filename, mode='a', header=False, index=False)


if __name__ == "__main__":

    from ant_colony import AntColony

    ant_colony_tests = AntColonyTests()
    # ant_colony_tests.get_glpk_tables(5)
    asyncio.run(ant_colony_tests.run_grid_search(output_filename=r'tests\output\results_grid_search.csv'))

