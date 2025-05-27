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
        return
    
    def communicate(self, package_size):
        targets = self.target
        if not targets:
            return False
    
        for node in self.node:
            node.sent_through = 0
            node.coverage.clear()
    
        send_mask = np.random.random(len(targets)) <= para.send_probability
        active_targets = np.array(targets)[send_mask]

        for target in active_targets:
            # Lấy danh sách sensor active
            sensors = [n[0] for n in target.listSensors if n[0].is_active]
            if not sensors:
                continue
                
            # Chọn sensor đầu tiên active và gửi
            sensor = sensors[0]
            sensor.coverage.append(target.id)
            package = Package(package_size=package_size)
            sensor.send(self, package, receiver=sensor.find_receiver(self))

            if package.is_success == False:
                return False
            
            if self.count_dead_node() != self.nb_dead:
                self.reset_neighbor()
        return True

    def run_per_second(self, t, optimizer):
        self.all_package = self.communicate(package_size=400)

        # Vector hóa kiểm tra năng lượng
        energies = np.array([node.energy for node in self.node])
        thresh = np.array([node.energy_thresh for node in self.node])
        request_mask = energies < thresh
        self.request_id = np.where(request_mask)[0].tolist()

        for idx in self.request_id:
            self.node[idx].request(index=idx, optimizer=optimizer, t=t)
        for idx in np.where(~request_mask)[0]:
            self.node[idx].is_request = False

        if optimizer and self.active:
            for mc in self.mc_list:
                mc.run(time_stem=t, net=self, optimizer=optimizer)

        self.calculate_charged_per_sec()

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
                with open(self.net_log_file, 'a') as f:
                    writer = csv.DictWriter(f, fieldnames=log_buffer[0].keys())
                    writer.writerows(log_buffer)                
                break

            # Ghi buffer khi đầy hoặc kết thúc
            if len(log_buffer) >= 100 or self.t == max_time:
                with open(self.net_log_file, 'a') as f:
                    writer = csv.DictWriter(f, fieldnames=log_buffer[0].keys())
                    writer.writerows(log_buffer)
                log_buffer.clear()

        print('\n[Network]: Finished with {} dead sensors, {} packages at {}s!'.format(self.count_dead_node(), self.count_package(), dead_time))
        return dead_time, self.nb_dead

    def simulate(self, optimizer=None, t=0, dead_time=0, max_time=604800):
        life_time, nb_dead = self.simulate_max_time(optimizer=optimizer, t=t, dead_time=dead_time, max_time=max_time)
        return life_time, nb_dead

    def print_net(self, func=to_string):
        func(self)

    def find_min_node(self):
        energies = np.array([node.energy for node in self.node])
        mask = (energies > 0)  # Chỉ xét node còn sống
        return np.argmin(energies[mask]) if np.any(mask) else -1
        
    def calculate_charged_per_sec(self, t=0):
        charged_added = np.array([node.charged_added for node in self.node])
        charged_count = np.array([node.charged_count for node in self.node])    
        
        # Vector hóa cập nhật
        charged_count += (charged_added > 0).astype(int)
        for i, node in enumerate(self.node):
            node.charged_count = charged_count[i]
            node.charged_added = 0

    def count_dead_node(self):
        return np.sum(np.array([node.energy <= 0 for node in self.node]))

    def get_average_energy(self):
        return np.mean([node.avg_energy for node in self.node])
    
    def _calculate_avg_used_and_charged(self):
        used = np.array([node.actual_used for node in self.node])
        charged = np.array([node.charged / node.charged_count if node.charged_count > 0 else 0 for node in self.node])
        cnt_node = np.sum([node.charged_count > 0 for node in self.node])
        return np.mean(used), np.mean(charged[charged > 0]) if cnt_node > 0 else 0