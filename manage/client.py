import grpc

from .codegen import manage_server_pb2, manage_server_pb2_grpc


class Client:
    @staticmethod
    def run(name, args=None):
        if args is None:
            args = {}
        with grpc.insecure_channel('localhost:32700') as channel:
            stub = manage_server_pb2_grpc.ManageStub(channel)
            peers = stub.run_command(manage_server_pb2.Command(name=name, args=args))
            for peer in peers:
                print(peer.line)
