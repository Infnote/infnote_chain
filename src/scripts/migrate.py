from blockchain import Database
from networking import PeerManager


def migrate():
    Database().migrate()
    PeerManager().migrate()
