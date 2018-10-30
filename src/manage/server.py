import grpc
import asyncio
import string
import getpass
import random

from calendar import timegm
from threading import Thread
from concurrent import futures

from .codegen.manage_server_pb2_grpc import ManageServicer, BlockchainServicer, \
    add_ManageServicer_to_server, add_BlockchainServicer_to_server
from .codegen.manage_server_pb2 import Result, Block

from scripts.generate import create_block

from blockchain import Blockchain
from sharing import ShareManager
from utils.reprutil import flat_dict_for_repr
from utils import settings


class ManageServer(ManageServicer):

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
            name=args.get('name', f'Chain-{"".join(random.choices(string.ascii_letters + string.digits, k=6))}'),
            version='0.1',
            author=args.get('author', getpass.getuser()),
            website=args.get('website', 'infnote.com'),
            email=args.get('email', 'vergil@infnote.com'),
            desc=args.get('desc', '')
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


class BlockchainServer(BlockchainServicer):

    def create_block(self, request, context):
        if request.chain_id is not None and len(request.chain_id) > 0:
            chain = Blockchain.load(request.chain_id)
            if chain is not None:
                try:
                    block = create_block(chain, request.content)
                    if block is not None:
                        return Block(
                            chain_id=block.chain_id,
                            block_hash=block.block_hash,
                            prev_hash=block.prev_hash,
                            signature=block.signature,
                            time=timegm(block.time.timetuple()),
                            height=block.height
                        )
                except ValueError:
                    pass
        return Block()


def run_rpc_server():
    def __run():
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        add_ManageServicer_to_server(ManageServer(), server)
        add_BlockchainServicer_to_server(BlockchainServer(), server)
        server.add_insecure_port(f'{settings.manage.address}:{settings.manage.port}')
        server.start()
        asyncio.set_event_loop(asyncio.new_event_loop())
        asyncio.get_event_loop().run_forever()
    Thread(target=__run).start()
