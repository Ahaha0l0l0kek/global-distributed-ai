class PeerRegistry:
    def __init__(self):
        self.peers = set()

    def add(self, host_port: str):
        self.peers.add(host_port)

    def get_all(self):
        return list(self.peers)

    def remove(self, host_port: str):
        self.peers.discard(host_port)