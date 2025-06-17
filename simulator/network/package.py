from simulator import parameters as para

class Package:
    def __init__(self, target_id, package_size=400):
        self.path = []
        self.target_id = target_id
        self.size = package_size
        self.is_success = False

    def update_path(self, node_id):
        self.path.append(node_id)