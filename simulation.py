import sys
import time
import pandas as pd
import numpy as np
from simulator import parameters as para
from simulator.import_network import Simulation

def setup_parameters(q_alpha=0.5, q_gamma=0.5, alpha=0.7, beta=0.1, gamma=0.1):
    para.q_alpha = q_alpha
    para.q_gamma = q_gamma

    para.energy_q = alpha
    para.connect_q = beta
    para.cover_q = gamma
    para.history_q = 1 - para.energy_q - para.connect_q - para.cover_q

'''
    simulation.py                                                           => Run hanoi1000n50_new x 1
    simulation.py testcase_name                                             => Run testcase_name x 3
    simulation.py testcase_name alpha(minmax) gamma(minmax)                 => Run tuning Q-learning parameters x 1
    simulation.py testcase_name alpha(minmax) beta(minmax) gamma(minmax)    => Run tuning Q-learning parameters x 1
'''

def RunOnce(testcase_name = 'hanoi1000n50', output_filename = 'hanoi1000n50_once'):
    sim = Simulation(f'data/{testcase_name}.yaml')
    sim.network_init()
    life_time, elapsed_time = sim.run_simulator(E_mc=108000, run_times=1, output_filename=output_filename)
    del sim
    return life_time, elapsed_time

def RunMultipleTimes(testcase_name = 'hanoi1000n50'):
    lifetime = []
    runtime = []

    start = time.time()
    life, elapsed = RunOnce(testcase_name=testcase_name, output_filename=testcase_name + 'run_multiple_times')
    end = time.time()
    
    lifetime = lifetime + life
    runtime = runtime + elapsed

    data = {
        'Lifetime': lifetime,
        'Runtime': runtime
    }

    df = pd.DataFrame(data)
    df.to_excel(f'{testcase_name}_output.xlsx', index=False, sheet_name='Data')
    print(f'Life time: {runtime} - Elapsed time: {end - start}')


def main():
    if len(sys.argv) == 1:
        print('Option 1: Chạy bộ test hanoi1000n50 x 1')
        RunOnce()
    elif len(sys.argv) == 2:
        testcase_name = sys.argv[1]
        print(f'Option 2: Chạy bộ test {testcase_name} x 3')
        RunMultipleTimes(testcase_name)
    elif len(sys.argv) == 6:
        testcase_name = sys.argv[1]
        for q_a in np.arange(float(sys.argv[2]), float(sys.argv[3]) + 0.1, 0.1):
            for q_g in np.arange(float(sys.argv[4]), float(sys.argv[5]) + 0.1, 0.1):
                setup_parameters(q_alpha=q_a, q_gamma=q_g)
                print(f'Option 3: Chạy bộ test {testcase_name} x 1 - q_alpha {q_a} - q_gamma {q_g}')
                RunOnce(testcase_name, output_filename=testcase_name + '_q_' + str(q_a) + '_' + str(q_g))
    elif len(sys.argv) == 8:
        testcase_name = sys.argv[1]
        for a in np.arange(float(sys.argv[2]), float(sys.argv[3]) + 0.1, 0.1):
            for b in np.arange(float(sys.argv[4]), float(sys.argv[5]) + 0.1, 0.1):
                for c in np.arange(float(sys.argv[6]), float(sys.argv[7]) + 0.1, 0.1):
                    setup_parameters(q_alpha=q_a, q_gamma=q_g)
                    print(f'Option 3: Chạy bộ test {testcase_name} x 1 - a {a} - b {b} - c {c} - d {1 - a - b - c}')
                    RunOnce(testcase_name, output_filename=testcase_name + '_r_' + str(a) + '_' + str(b) + '_' + str(c)) 

if __name__ == "__main__":
    main()
