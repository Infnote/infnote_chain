class PeerConnection:

    def __init__(self, peer_id, host, port, sock, protocol_version=None, client_id=None, server_address=None):
        self.peer_id = peer_id
        self.host = host
        self.port = port
        self.sock = sock
        self.protocol_version = protocol_version
        self.client_id = client_id
        self.produce_actions = []
        self.server_listening = server_address

    def close(self):
        pass

    def send_data(self, msg_type, msg_data):
        pass

    async def send_data_json(self, msg):
        await self.sock.send(msg)

    def rcv_data(self):
        pass

    async def rcv_data_json(self):
        response = await self.sock.recv()
        return response

    def __make_msg(self, msg_type, msg_data):
        pass

    def __str__(self):
        # --------------------------------------------------------------------------
        return "|%s|" % self.peer_id
