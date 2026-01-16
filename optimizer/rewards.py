# Libraries
import numpy as np
from scipy.spatial import distance

from simulator.network.info import Network
from simulator.mobilecharger.info import MobileCharger

from simulator import parameters as para
from optimizer.utils import get_charging_time, get_charge_per_sec, penalty_reward

BASE = -1

def q_max_function(q_table):
    temp = [max(row) for index, row in enumerate(q_table)]
    return np.asarray(temp)
    
def reward_function(network: Network, mc: MobileCharger, q_learning, state, time_stem):
    theta = q_learning.theta
    charging_time = get_charging_time(network, mc, q_learning, time_stem=time_stem, state=state, theta=theta)
    w, nb_target_alive = get_weight(network, mc, q_learning, state, charging_time)

    p = get_charge_per_sec(network, q_learning, state)
    p_hat = p / (np.sum(p) + 10 ** -3)
    E = []
    e = []

    for node in network.node:
        if node.is_active == True:
            E.append(node.energy)
            e.append(node.avg_energy)
    
    E = np.asarray(E)
    e = np.asarray(e)
    E_safe = np.maximum(E, 1e-9)

    second = len(nb_target_alive) / len(network.target)
    third = np.sum(w * p_hat)
    first = np.sum(e * p / E_safe)

    return first, second, third, charging_time

def additional_reward_function(network: Network, mc: MobileCharger, q_learning):
    fourth = np.append(network.clusters.charging_history_reward(network), [0])      # No history for depot
    fifth = penalty_reward(network, mc, q_learning)

    return fourth, fifth

def init_function(nb_action=para.n_clusters):
    return np.zeros((nb_action + 1, nb_action + 1), dtype=float)

def get_weight(net, mc, q_learning, action_id, charging_time):
    p = get_charge_per_sec(net, q_learning, action_id)
    time_move = distance.euclidean(q_learning.action_list[mc.state], q_learning.action_list[action_id]) / mc.velocity
    request_id = []
    list_dead = []
    w = [0 for node in net.node if node.is_active == True]
    nb_target_alive = []

    for request in q_learning.list_request:
        request_id.append(request["id"])

    idx = 0    
    for node in net.node:
        if node.is_active == True and node.id in request_id:
            temp = (node.energy - time_move * request["avg_energy"]) + (p[idx] - request["avg_energy"]) * charging_time
            if temp < 0:
                list_dead.append(node.id)

    for node in net.node:
        if node.is_active == True and not node.id in list_dead:
            w[idx] = node.sent_through
            idx += 1
        
        if not node.id in list_dead and distance.euclidean(node.location, q_learning.action_list[action_id]) <= para.cha_ran:
            nb_target_alive.extend(node.coverage)


    total_weight = sum(w) + len(w) * 10 ** -3
    w = np.asarray([(item + 10 ** -3) / total_weight for item in w])     
    nb_target_alive = list(set(nb_target_alive))
    return w, nb_target_alive