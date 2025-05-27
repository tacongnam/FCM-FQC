import json
import yaml
import copy
import sys
import argparse

def ConvertNetwork(old_network, name):
    connector_node = []

    for node_p in old_network.nodes:
        node = {
            'cluster_id': 0, 
            'location': node_p
        }
        connector_node.append(node)

    data = {
        'Clusters': [
            {
                "centroid": [500.0, 500.0],
                "cluster_id": 0,
                "list_targets": old_network.targets
            }
        ],
        'ConnectorNode': connector_node,
        'InNode': [],
        'OutNode': [],
        'RelayNode': [],
        'SensorNode': [],
        'nodes': []
    }

    data['node_phy_spe'] = dict()
    data['node_phy_spe']['sen_range'] = 40.0
    data['node_phy_spe']['com_range'] = 80.0
    data['node_phy_spe']['capacity'] = 10800
    data['node_phy_spe']['efs'] = 1.0e-08
    data['node_phy_spe']['emp'] = 1.3e-12
    data['node_phy_spe']['er'] = 0.0001
    data['node_phy_spe']['et'] = 5.0e-05
    data['node_phy_spe']['package_size'] = 400.0
    data['node_phy_spe']['prob_gp'] = 1
    data['node_phy_spe']['threshold'] = 540

    data['seed'] = 0
    data['max_time'] = 604800
    data['Rc'] = 80.0
    data['Rs'] = 40.0

    data['base_station'] = old_network.base

    with open(f'data/{name}.yaml', 'w') as file:
        yaml.dump(data, file)
        print(f'Saved successly at data/{name}.yaml')

class OldNetwork:
    def __init__(self, filename):
        with open(f'data/{filename}.json', 'r') as file:
            self.net_argc = json.load(file)
        print(f'Load successfully at data/{filename}.json')

    def ImportOldNetwork(self):
        net_argc = copy.deepcopy(self.net_argc)
        self.nodes_sensor = net_argc["sensors"]
        self.nodes_relay = net_argc["relays"]
        print(f'Number of sensors: {len(self.nodes_sensor)}; number of relays: {len(self.nodes_relay)}')
        self.nodes = self.nodes_sensor + self.nodes_relay
        self.targets = net_argc["targets"]
        self.base = net_argc["base"]

def main(name):
    old_network = OldNetwork(name)
    old_network.ImportOldNetwork()
    ConvertNetwork(old_network, name)

parser = argparse.ArgumentParser(description='Model input')
parser.add_argument('--name', metavar='name', type=str, dest="filename",
                    help='filename')

args = parser.parse_args()

if __name__ == "__main__":
    main(args.filename)

