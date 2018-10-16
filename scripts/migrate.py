from blockchain import Database
from networking import PeerManager

Database().migrate()
PeerManager().migrate()
