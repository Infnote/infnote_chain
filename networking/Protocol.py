import json
from Services import services


def check_hello(message, p2p_version_peer):
    print("Message in Check_Hello:")
    print(message)
    if not services.is_json(message):
        return None
    msg_json = json.loads(message)
    if 'type' not in msg_json or 'p2pVersion' not in msg_json or 'clientId' not in msg_json \
            or 'listenPort' not in msg_json or 'nodeId' not in msg_json:
        return None
    if msg_json['p2pVersion'] != p2p_version_peer or msg_json['type'].upper() != "HELLO":
        return None
    return msg_json


def check_status(message):
    if not services.is_json(message):
        return None
    msg_json = json.loads(message)
    if 'type' not in msg_json or 'genesisHash' not in msg_json:
        return None
    if msg_json['type'].upper() != "STATUS":
        return None
    # Check Blockchain Information
    return msg_json


def check_addr(message):
    if not services.is_json(message):
        return None
    msg_json = json.loads(message)
    if 'type' not in msg_json or 'host' not in msg_json or 'port' not in msg_json:
        return None
    if msg_json['type'].upper() != "ADDR":
        return None
    # Maybe check ip address here
    return msg_json


def status_event():
    return json.dumps({'type': 'STATUS', 'genesisHash': "0000"})


def get_addr_event():
    return json.dumps({'type': 'GET_ADDR'})


def addr_event(host, port):
    return json.dumps({'type': 'ADDR', 'host': host, 'port': str(port)})


def handshaking_event(protocol_version, client_version, server_port, my_id):
    return json.dumps({'type': 'HELLO', 'p2pVersion': protocol_version, 'clientId': client_version,
                       'listenPort': server_port, 'nodeId': my_id})