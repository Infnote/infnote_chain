import grpc
import asyncio
import os
import signal
import string
import getpass

from datetime import datetime
from concurrent import futures
from sharing import ShareManager

from .codegen.manage_server_pb2_grpc import ManageServicer, add_ManageServicer_to_server
from .codegen.manage_server_pb2 import Result

from scripts.generate import create_block

from blockchain import Blockchain
from utils.reprutil import flat_dict_for_repr
from utils import settings


class Server(ManageServicer):

    def run_command(self, request, context):
        if request.name is not None:
            func = getattr(self, request.name)
            if func is not None:
                return func(request.args)
            else:
                def result():
                    yield Result(line=f'Command `{request.name}` not found.')
                return result()

    @staticmethod
    def peers(_):
        for peer in ShareManager().servers + ShareManager().clients:
            yield Result(line=f'{peer}')

    @staticmethod
    def create_chain(args):
        chain = Blockchain.create(
            name=f'Test Chain (by python @ {datetime.now().strftime("%Y-%m-%d %H:%M:%S")})',
            version='0.1',
            author=getpass.getuser(),
            website='infnote.com',
            email='vergil@infnote.com',
            desc=args.get('desc')
        )
        yield Result(line=flat_dict_for_repr(chain.info))

    def create_block(self, args):
        # IMPORTANT: delete these lines ↓↓↓ after test
        chains = [chain for chain in Blockchain.all_chains() if chain.is_owner]
        if len(chains) == 0:
            yield Result(line=f'You do not own any chains. Please create a chain first.')
        chain = chains[0]
        # IMPORTANT: delete these lines ↑↑↑

        size = self.parse_size(args.get('size', '0'))
        if size < 0:
            yield Result(line=f'"{args.get("size")}" is not a size.')
        else:
            yield Result(line=f'Block created:\n{create_block(chain, size)}')

    def create_blocks(self, args):
        # IMPORTANT: delete these lines ↓↓↓ after test
        chains = [chain for chain in Blockchain.all_chains() if chain.is_owner]
        if len(chains) == 0:
            yield Result(line=f'You do not own any chains. Please create a chain first.')
        chain = chains[0]
        # IMPORTANT: delete these lines ↑↑↑

        size = self.parse_size(args.get('size', '0'))
        count = args.get('count', 0)
        try:
            count = int(count)
        except ValueError:
            yield Result(line=f'"{count}" is not a number.')
        for i in range(count):
            yield Result(line=f'Block created:\n{create_block(chain, size)}')

    @staticmethod
    def parse_size(size):
        n = 1
        number = size[:-1]
        last = size[-1:]
        if last == 'b':
            n = 1
        elif last == 'k':
            n = 1024
        elif last == 'm':
            n = 1024 ** 2
        elif last in string.digits:
            number = size
        try:
            number = int(number) * n
        except ValueError:
            return -1
        return number

    @classmethod
    def run(cls):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        add_ManageServicer_to_server(cls(), server)
        server.add_insecure_port(f'{settings.manage.address}:{settings.manage.port}')
        server.start()
        try:
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            os.kill(os.getpid(), signal.SIGTERM)
