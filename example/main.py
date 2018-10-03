import random
import string

from pprint import PrettyPrinter
from blockchain import *


pprint = PrettyPrinter(indent=4).pprint

# Call migrate when first run

# Database().migrate()


# Create a new chain with information

# chain = Blockchain.create(
#     name='Python Chain (' + ''.join(random.choices(string.digits + 'abcdef', k=6)) + ')',
#     version='0.1',
#     author='Vergil Choi',
#     website='infnote.com',
#     email='vergil@infnote.com'
# )


# Get all saved chains

pprint([chain.info for chain in Blockchain.all_chains()])

