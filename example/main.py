# import random
# import string

from pprint import PrettyPrinter
from blockchain import *


pprint = PrettyPrinter(indent=4).pprint

# Call migrate when first run, it will create indexes for accelerating query speed
# Database().migrate()


# Create a new chain with information
# chain = Blockchain.create(
#     name='Python Chain (' + ''.join(random.choices(string.digits + 'abcdef', k=6)) + ')',
#     version='0.1',
#     author='Vergil Choi',
#     website='infnote.com',
#     email='vergil@infnote.com',
#     desc='Example chain for python code test.'
# )


# Get all saved chains
pprint([chain.info for chain in Blockchain.all_chains()])

# Receive a block
block = Block({
    'chain_id': 'QvCAeP8b6oGYwc5EGmUdnSwN2wLuGBFcm3DN1RADC87KjLstZigsVDkvz3YsjfBkqxcVQRTir6aiTnvg2ssc4Qxi',
    'hash': '25r7uNHrXHNPmT8hNH5cmDCVdv2TqTvW4aGYWQQps7MX',
    'height': 0,
    'payload': '{\"author\":\"Vergil Choi\",\"desc\":\"Created on iOS.\",\"email\":\"vergil@infnote.com\",' 
               '\"name\":\"Swift Chain\",\"version\":\"0.1\",\"website\":\"infnote.com\"}',
    'signature': '381yXYiPHmgFM2wLXx3MrSxzso4hWsnRYub7hdzi18agv1eLNvLz2mQ7C91d1Ktw3hyDUFjBjssEdgkJDTjkazvfc5TWW1AX',
    'time': 1538562151
})


# Check the block
if block.is_valid:
    print('Valid block received.')
else:
    print('Invalid block received.')


# Create a instance for exist chain
key = Key(block.chain_id)
chain = Blockchain(key)
print('Chain ID: ' + chain.id)
print('Owner: ' + ('YES' if chain.is_owner else 'NO'))


# Save chain (only public key and private key if valid) into database
# It will check if the chain is already database
is_saved = chain.save()
print('Chain saved.' if is_saved else 'Chain is already in database.')


# Save block into database, it will check if the block is valid for this chain before saving
is_saved = chain.save_block(block)
print('Block saved.' if is_saved else 'Block failed to save.')


# Load a block from database by height in specific chain
block = chain.get_block(0)
# Or by block hash
# block = chain.get_block(block_hash='96f7cwpawVQ8m5zfc1VRz7b1kqNPHLzHnXVVMCRG4uHy')


# Get encoded data of a block
if block is not None:
    print(block.data)
