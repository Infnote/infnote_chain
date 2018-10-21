import grpc
import asyncio
import os
import signal
import string

from concurrent import futures
from sharing import ShareManager

from .codegen.manage_server_pb2_grpc import ManageServicer, add_ManageServicer_to_server
from .codegen.manage_server_pb2 import Result

from scripts.generate import create_block


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

    def create_block(self, args):
        size = self.parse_size(args.get('size', '0'))
        if size < 0:
            yield Result(line=f'"{args.get("size")}" is not a size.')
        else:
            yield Result(line=f'Block created:\n{create_block(size)}')

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
        server.add_insecure_port('localhost:32700')
        server.start()
        try:
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            os.kill(os.getpid(), signal.SIGTERM)
