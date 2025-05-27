import csv
import numpy as np
from simulator.network.package import Package
from simulator import parameters as para

def to_string(net):
    min_energy = 10 ** 10
    min_node = -1
    for node in net.node:
        if node.energy < min_energy:
            min_energy = node.energy
            min_node = node
    min_node.print_node()

def show_info(network=None, mi=0, avg=0, cha=0, past_dead=0, optimizer=None):
    if network != None:
        print("\n[Network] Simulating time: {}s, lowest energy node: {:.4f}, used: {:.4f}, charged: {:.4f} at {} (id = {})".format(network.t, network.node[mi].energy, network.node[mi].actual_used, network.node[mi].charged, network.node[mi].location, mi))
        print('\t\t-----------------------')
        print('\t\tAverage used of each node: {:.6f}, average each node per second: {:.6f}'.format(avg, avg / network.t))
        print('\t\tAverage charged of each node this second: {:.6f}'.format(cha))
        print('\t\tNumber of dead nodes: {}'.format(past_dead))
        print('\t\t-----------------------\n')

        for mc in network.mc_list:
            print("\t\tMC #{} is {} at {} with energy {}".format(mc.id, mc.get_status(), mc.current, mc.energy))
                
        network_info = {
            'time_stamp' : network.t,
            'number_of_dead_nodes' : past_dead,
            'lowest_node_energy': round(network.node[mi].energy, 3),
            'lowest_node_location': network.node[mi].location,
            'theta': optimizer.theta,     
            'avg_energy': network.get_average_energy(),
            'average_used_of_each_node': avg,
            'average_used_of_each_node_this_second': avg / network.t,
            'average_charged_of_each_node_per_time': cha,
                
            'MC_0_status' : network.mc_list[0].get_status(),
            'MC_1_status' : network.mc_list[1].get_status(),
            'MC_2_status' : network.mc_list[2].get_status(),
            'MC_0_location' : network.mc_list[0].current,
            'MC_1_location' : network.mc_list[1].current,
            'MC_2_location' : network.mc_list[2].current,
        }
            
        with open(network.net_log_file, 'a') as information_log:
            node_writer = csv.DictWriter(information_log, fieldnames=['time_stamp', 'number_of_dead_nodes', 'lowest_node_energy', 'lowest_node_location', 'theta', 'avg_energy', 'average_used_of_each_node', 'average_used_of_each_node_this_second', 'average_charged_of_each_node_per_time', 'MC_0_status', 'MC_1_status', 'MC_2_status', 'MC_0_location', 'MC_1_location', 'MC_2_location'])
            node_writer.writerow(network_info)