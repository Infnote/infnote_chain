import os


class AddressManager:

    def __init__(self, db_file=None):
        if db_file is None:
            db_file = "peers.dat"
        self.peers_db = db_file
        self.new_peer_console = None
        # AddressManager will maybe store a profile foreach node;
        # Profile: a grade (speed, sanctions, frequency only) and the last activity

        # Set of peers address
        self.peers_known = set()

    def add_node_console(self, new_peer):
        self.new_peer_console = new_peer

    def fill_peers_db(self, peer):
        found = False
        if not os.path.exists(self.peers_db):
            open(self.peers_db, "w")
        with open(self.peers_db, 'r+') as peers:
            for node_peer in peers:
                if node_peer == peer + '\n' or node_peer == peer:
                    found = True
                    break
            if not found:
                peers.write(peer + '\n')

    def peers_discovery(self):
        # This function will try different peer discovery methods
        self.peers_known = read_peers_db(self.peers_db)
        if self.new_peer_console is not None:
            self.peers_known.add(self.new_peer_console)


def read_peers_db(db_file):
    # Parse the file before
    peers_list = []
    if os.path.exists(db_file):
        peers_list = [line.rstrip('\n') for line in open(db_file)]
    return set(peers_list)
