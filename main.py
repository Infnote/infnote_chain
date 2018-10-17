import argparse
import sys

from sharing import ShareManager, PeerManager, Peer
from scripts.migrate import migrate
from utils.logger import default_logger as log


class Main:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description='Infnote Chain')

        server_group = self.parser.add_argument_group('Server')
        server_group.add_argument('-s', '--start', action='store_true',
                                  help='Start server and connect to P2P network.')
        server_group.add_argument('-f', '--fork', action='store_true',
                                  help='Start service in background fork process.')
        server_group.add_argument('-a', '--add', type=str, help='Add a peer to database.')

        migrate_group = self.parser.add_argument_group('Migrate')
        migrate_group.add_argument('-m', '--migrate', action='store_true',
                                   help='Run migration for blockchain and peers storage.')

    def run(self, args):
        if len(args) == 0:
            self.parser.print_help()
            return
        parsed = self.parser.parse_args(args)
        if parsed.migrate:
            self.migrate()
        elif parsed.start:
            self.server()
        elif parsed.add:
            self.add_peer(parsed.add)

    @staticmethod
    def migrate():
        migrate()

    @staticmethod
    def server():
        ShareManager().start()
        log.info(PeerManager())

    @staticmethod
    def add_peer(arg):
        addr = arg.split(':')
        if len(addr) < 2:
            print('Wrong format of peer address. It should be like "127.0.0.1:8080".')
        peer = Peer(address=addr[0], port=int(addr[1]))
        PeerManager().add_peer(peer)
        print(f'Peer saved: {peer}')


if __name__ == '__main__':
    Main().run(sys.argv[1:])
