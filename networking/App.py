import sys
import Peer
import signal
import _thread


class App:

    def __init__(self):
        self.peer = Peer.Peer(self)
        self.max_peers = 100

    def __add_node_console(self):
        new_node = None
        if (len(sys.argv) > 2 and sys.argv[2] == '-add_node') or len(self.peer.get_peers()) == 0:
            try:
                new_node = input('Enter address and port:')
            except SyntaxError:
                node = None
            except KeyboardInterrupt:
                exit(0)
            if new_node is None or len(new_node) == 0:
                print("Address it not valid, no peer connected...")
            else:
                self.peer.addr_manager.add_node_console(new_node)

    def run(self):
        self.__add_node_console()
        if len(sys.argv) > 1:
            self.peer.server_port = int(sys.argv[1])
        self.run_peer()

    def connect_new_peer(self, peer_addr):
        # This method should be call also to check on a queue of clients to connect
        # Then if a peer wants to add more peers (ex: Peer without known_peers at the beginning)
        _thread.start_new_thread(self.peer.run_client, (peer_addr, ))

    def run_peer(self):
        # This restores the default Ctrl+C signal handler, which just kills the process
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        _thread.start_new_thread(self.peer.run_server, ())
        # Peers discovery
        self.peer.addr_manager.peers_discovery()
        # Iterate through the list of known peer and connect new peer
        # until the end of the known peer list or until the number of max peers connected is not reached
        for peer_addr in self.peer.addr_manager.peers_known:
            if len(self.peer.peers_co) >= self.max_peers:
                break
            self.connect_new_peer(peer_addr)
        # Client logic in the future : Example Send message on this channel
        while self.peer.shutdown is False:
            action = input("Type:")
            self.app_client(action)
            pass

    def app_client(self, action):
        # App client logic
        if action == "GET_ADDR" and len(self.peer.peers_co) > 0:
            self.broadcast_get_addr()

    def broadcast_get_addr(self):
        print("Will Send A GET_ADDR")
        for peer_connected in self.peer.peers_co:
            peer_connected.produce_actions.append('GET_ADDR')


if __name__ == '__main__':
    app = App()
    app.run()
