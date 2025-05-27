from simulator import parameters as para

class Package:
    def __init__(self, package_size=400):
        self.path = []
        self.size = package_size

    def update_path(self, node_id):
        self.path.append(node_id)