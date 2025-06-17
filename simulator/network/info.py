import csv
from scipy.spatial import distance
import numpy as np

from simulator import parameters as para
from simulator.network.utils import to_string, show_info
from optimizer.fuzzycmeans import Clusters
from simulator.network.package import Package

class Network:
    def __init__(self, list_node=None, mc_list=None, target=None, experiment=None, com_range=0, list_clusters=None):
        self.node = list_node
        self.base_range = []
        self.reset_neighbor()

        self.all_package = True
        self.nb_dead = 0

        self.mc_list = mc_list
        self.target = target

        self.listClusters = list_clusters

        self.active = False
        self.com_range = com_range

        self.clusters = Clusters()

        self.experiment = experiment
        self.net_log_file = "log/net_log_" + self.experiment + ".csv"
        self.mc_log_file = "log/mc_log_" + self.experiment + ".csv"
        self.request_id = []

        self.t = 0
        
        for t in self.target:
            for n in self.node:
                if distance.euclidean(n.location, t.location) < n.sen_ran:
                    n.listTargets.append(t)
                    t.listSensors.append((n, distance.euclidean(n.location, t.location)))
            
            t.listSensors = sorted(t.listSensors, key=lambda x: x[1])
    
    def reset_neighbor(self):
        # Reset neighbor list
        for node in self.node:
            if node.is_active == True:
                node.probe_neighbors(self)
        
        # Reset level list
        for node in self.node:
            node.level = -1
        tmp1 = []
        tmp2 = []

        if len(self.base_range) == 0:
            for node in self.node:
                if distance.euclidean(node.location, para.base) <= node.com_ran and node.is_active == True:
                    node.level = 1
                    tmp1.append(node)
            self.base_range = tmp1
        else:
            tmp1 = self.base_range

        while True:
            if len(tmp1) == 0:
                break

            for node in tmp1:
                for neighbor in node.potentialSender:
                    if neighbor.is_active == True and neighbor.level == -1:
                        neighbor.level = node.level + 1
                        tmp2.append(neighbor)
            tmp1 = tmp2[:]
            tmp2.clear()

        for node in self.node:
            if node.level == -1:
                node.is_active = False   
        return
    
    def communicate(self, package_size):
        targets = self.target
        if not targets:
            return False
    
        for node in self.node:
            node.sent_through = 0
            node.coverage.clear()
    
        for id, target in enumerate(targets):
            # Lấy danh sách sensor active
            sensors = [n[0] for n in target.listSensors if n[0].is_active]
            if not sensors:
                continue
                
            # Chọn sensor đầu tiên active và gửi
            sensor = sensors[0]
            sensor.coverage.append(target.id)
            
            package = Package(target_id=target.id, package_size=package_size)
            receiver=sensor.find_receiver(self)

            if (receiver.id != -1) or (receiver.id == -1 and sensor in self.base_range):
                sensor.send(self, package, receiver)
            else:
                assert receiver.id == -1

            if package.is_success == False:
                return False
            
            if self.count_dead_node() != self.nb_dead:
                print(f'nb_node change: {self.nb_dead} -> {self.count_dead_node()}')
                self.nb_dead = self.count_dead_node()
                self.reset_neighbor()
        return True

    def run_per_second(self, t, optimizer):
        # Send package
        self.all_package = self.communicate(package_size=400)

        for idx, node in enumerate(self.node):
            if node.is_active == True and node.energy < node.energy_thresh:
                node.request(index = idx, optimizer = optimizer, t=t)
            else:
                node.is_request = False

        if optimizer and self.active:
            for mc in self.mc_list:
                mc.run(time_stem=t, net=self, optimizer=optimizer)

    def simulate_max_time(self, optimizer=None, t=0, dead_time=0, max_time=604800):
        print('Simulating...')
        self.nb_dead = self.count_dead_node()
        self.all_package = self.communicate(package_size=0)

        dead_time = dead_time
        
        if t == 0:
            with open(self.net_log_file, "w") as f:
                writer = csv.DictWriter(f, fieldnames=['time_stamp', 'number_of_dead_nodes', 'lowest_node_energy', 'lowest_node_location', 'theta', 'avg_energy', 'average_used_of_each_node', 'average_used_of_each_node_this_second', 'average_charged_of_each_node_per_time', 'MC_0_status', 'MC_1_status', 'MC_2_status', 'MC_0_location', 'MC_1_location', 'MC_2_location'])
                writer.writeheader()
            with open(self.mc_log_file, "w") as f:
                writer = csv.DictWriter(f, fieldnames=['time_stamp', 'id', 'starting_point', 'destination_point', 'decision_id', 'charging_time', 'moving_time'])
                writer.writeheader()
        
        self.t = t
        if self.all_package == False:
            print("Not enough packages received from BS!")
            return dead_time, self.nb_dead
        
        log_buffer = []  # Buffer để giảm số lần ghi file

        while self.t <= max_time:
            self.t = self.t + 1

            # Create clusters
            if self.t % para.update_time == 0:
                if self.active == False:
                    for s in self.node:
                        s.update_average_energy()

                    self.clusters.fuzzy_c_means(self)
                    optimizer.action_list = self.clusters.get_charging_pos()
                    self.active = True
                else:
                    self.clusters.update_centers()
                    optimizer.action_list = self.clusters.get_charging_pos()
                    for s in self.node:
                        s.update_average_energy()

            # Print logs
            if (self.t - 1) % 1000 == 0:
                mi = self.find_min_node()
                avg, cha = self._calculate_avg_used_and_charged()
                show_info(self, mi, avg, cha, self.nb_dead, optimizer)

            # Run algorithm
            self.run_per_second(self.t, optimizer)

            # If network is dead
            if self.all_package == False:
                dead_time = self.t
                for mc in self.mc_list:
                    mc.flush_buffer(self.mc_log_file)
                break

        print('\n[Network]: Finished with {} dead sensors at {}s!'.format(self.nb_dead, dead_time))
        return dead_time, self.nb_dead

    def simulate(self, optimizer=None, t=0, dead_time=0, max_time=604800):
        life_time, nb_dead = self.simulate_max_time(optimizer=optimizer, t=t, dead_time=dead_time, max_time=max_time)
        return life_time, nb_dead

    def print_net(self, func=to_string):
        func(self)

    def find_min_node(self):
        max_node = self.node[0].energy_max
        max_id = -1
        for node in self.node:
            if node.is_active == True and node.energy < max_node:
                max_node = node.energy
                max_id = node.id
        return max_id
        
    def count_dead_node(self):
        return np.sum(np.array([node.energy <= 0 for node in self.node]))

    def get_average_energy(self):
        avg_energy = 0
        count = 0
        for node in self.node:
            if node.is_active == True:
                avg_energy += node.avg_energy
                count += 1
        if count > 0:
            return avg_energy / count
        else:
            return 0
    
    def _calculate_avg_used_and_charged(self):
        used = np.array([node.actual_used for node in self.node])
        charged = np.array([node.charged / node.charged_count if node.charged_count > 0 else 0 for node in self.node])
        cnt_node = np.sum([node.charged_count > 0 for node in self.node])
        return np.mean(used), np.mean(charged[charged > 0]) if cnt_node > 0 else 0