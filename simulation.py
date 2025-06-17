import sys
import time
import argparse
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


def RunOnce(testcase_name = 't_50', output_filename = 't_50', run_times = 1):
    sim = Simulation(f'data/{testcase_name}.yaml')
    sim.network_init()
    life_time, elapsed_time = sim.run_simulator(E_mc=108000, run_times=run_times, output_filename=output_filename)
    del sim
    return life_time, elapsed_time

def RunMultipleTimes(testcase_name = 't_50', run_time=15):
    lifetime = []
    runtime = []

    start = time.time()
    life, elapsed = RunOnce(testcase_name=testcase_name, output_filename=testcase_name + 'run_multiple_times', run_times=run_time)
    end = time.time()

    data = {
        'Lifetime': life,
        'Runtime': elapsed
    }

    df = pd.DataFrame(data)
    df.to_excel(f'{testcase_name}_output.xlsx', index=False, sheet_name='Data')
    print(f'Life time: {runtime} - Elapsed time: {end - start}')


parser = argparse.ArgumentParser(description='Simulation input')
parser.add_argument('--t', metavar='type', type=int, dest="type",
                    help='simulation type: [0 default run once] [1 run three times] [2 run q test] [3 run reward test]', default=0)
parser.add_argument('--n', metavar='name', type=str, dest="name",
                    help='testcase name: [default t_50]', default='t_50')
parser.add_argument('--rt', metavar='runtime', type=int, dest='runtime',
                    help='run times', default=15)
parser.add_argument('--amin', metavar='alpha_min', type=float, dest="alpha_min",
                    help='alpha_min')
parser.add_argument('--amax', metavar='alpha_max', type=float, dest="alpha_max",
                    help='alpha_max')
parser.add_argument('--bmin', metavar='beta_min', type=float, dest="beta_min",
                    help='beta_min')
parser.add_argument('--bmax', metavar='beta_max', type=float, dest="beta_max",
                    help='beta_max')
parser.add_argument('--gmin', metavar='gamma_min', type=float, dest="gamma_min",
                    help='gamma_min')
parser.add_argument('--gmax', metavar='gamma_max', type=float, dest="gamma_max",
                    help='gamma_max')

args = parser.parse_args()

def main():
    if args.type == 0:
        RunOnce()
    elif args.type == 1:
        print(f'Option 2: Chay bo test {args.name}')
        RunMultipleTimes(args.name, args.runtime)
    elif args.type == 2:
        for q_a in np.arange(args.alpha_min, args.alpha_max + 0.1, 0.1):
            for q_g in np.arange(args.gamma_min, args.gamma_max + 0.1, 0.1):
                setup_parameters(q_alpha=q_a, q_gamma=q_g)
                print(f'Option 3: Chay bo test {args.name} x 1 - q_alpha {q_a} - q_gamma {q_g}')
                RunOnce(args.name, output_filename=args.name + '_q_' + str(q_a) + '_' + str(q_g))
    elif args.type == 3:
        for a in np.arange(args.alpha_min, args.alpha_max + 0.1, 0.1):
            for b in np.arange(args.beta_min, args.beta_max + 0.1, 0.1):
                for c in np.arange(args.gamma_min, args.gamma_max + 0.1, 0.1):
                    setup_parameters(q_alpha=q_a, q_gamma=q_g)
                    print(f'Option 4: Chay bo test {args.name} x 1 - a {a} - b {b} - c {c} - d {1 - a - b - c}')
                    RunOnce(args.name, output_filename=args.name + '_r_' + str(a) + '_' + str(b) + '_' + str(c)) 

if __name__ == "__main__":
    main()
