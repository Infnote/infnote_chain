import argparse
import sys
import os
import signal
import logging

from collections import namedtuple
from sharing import ShareManager, PeerManager, Peer
from scripts.migrate import migrate
from utils.logger import default_logger as log
from utils import settings


class Main:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description='Infnote Chain')
        self.subparsers = self.parser.add_subparsers(dest='command')

        self.server_commands = self.subparsers.add_parser('server', help='Server relevant commands.')
        self.server_commands.set_defaults(func=self.server)
        self.server_subs = self.server_commands.add_subparsers(dest='subcommand')
        sub = self.server_subs.add_parser('start', help='Start server.')
        sub.set_defaults(func=self.start_server)
        sub.add_argument('-f', '--fork', action='store_true', help='Start server in background.')
        self.server_subs\
            .add_parser('restart', help='Restart background server.')\
            .set_defaults(func=self.restart_server)
        self.server_subs\
            .add_parser('stop', help='Stop server which is running in background.')\
            .set_defaults(func=self.stop_server)

        self.migrate_commands = self.subparsers.add_parser('migrate', help='Do migrations on MongoDB.')
        self.migrate_commands.set_defaults(func=self.migrate)
        self.migrate_subs = self.migrate_commands.add_subparsers(dest='subcommand')
        sub = self.migrate_subs.add_parser('add', help='Add peer to database.')
        sub.add_argument('address', type=str, help='Peer address (eg. 127.0.0.1:32767)')
        sub.add_argument('-s', '--self', action='store_true', help='Add current host as a peer to database.')
        sub.set_defaults(func=self.add_peer)

        self.shell_commands = self.subparsers.add_parser('shell', help='Connect to background process.')
        self.shell_commands.set_defaults(func=self.shell)

    def run(self, args):
        args = self.parser.parse_args(args)
        if args.command is None:
            self.parser.print_help()
        else:
            args.func(args)

    def server(self, _):
        self.server_commands.print_help()

    @staticmethod
    def start_server(args):
        if args.fork:
            pid = os.fork()
            if pid == 0:
                for handler in list(log.handlers):
                    if not isinstance(handler, logging.FileHandler):
                        log.removeHandler(handler)

                log.info(f'Running with PID {os.getpid()}')
                log.info(PeerManager())
                ShareManager().start()
                with open('/tmp/infnote_chain.pid', 'w+') as file:
                    file.write(f'{os.getpid()}')
            else:
                log.info('Infnote Chain P2P Network Started in child process.')
        else:
            log.info(PeerManager())
            ShareManager().start()

    @staticmethod
    def stop_server(_=None):
        try:
            with open('/tmp/infnote_chain.pid', 'r') as file:
                pid = int(file.readline())
                os.kill(pid, signal.SIGTERM)
                log.info(f'Killed server by PID {pid}')
        except FileNotFoundError:
            log.warning('PID file is not exist. Process may not startup correctly.')
        except ProcessLookupError:
            log.warning(f'No such process PID {pid}.')

    def restart_server(self, _):
        self.stop_server()
        self.start_server(namedtuple('args', ['fork'])(fork=True))

    @staticmethod
    def migrate(_):
        migrate()

    def add_peer(self, args):
        if args.self:
            peer = Peer(address=settings.server.address, port=settings.server.port)
        elif args.address is not None:
            addr = args.address.split(':')
            if len(addr) < 2:
                print('Wrong format of peer address. It should be like "127.0.0.1:32767".')
            peer = Peer(address=addr[0], port=int(addr[1]))
        else:
            self.migrate_commands.print_help()
            return
        PeerManager().add_peer(peer)
        log.info(f'Peer saved: {peer}')


if __name__ == '__main__':
    Main().run(sys.argv[1:])
