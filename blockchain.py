import hashlib
import json
from time import time
from uuid import uuid4

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_votes = []
        # Create the genesis block
        self.new_block(previous_hash='1', proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain
        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'votes': self.current_votes,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of votes
        self.current_votes = []

        self.chain.append(block)
        return block

    def new_vote(self, voter_id_hash, candidate_id):
        """
        Creates a new vote to go into the next mined Block
        :param voter_id_hash: <str> Hashed ID of the Voter
        :param candidate_id: <str> ID of the Candidate
        :return: <int> The index of the Block that will hold this vote
        """
        self.current_votes.append({
            'voter_id_hash': voter_id_hash,
            'candidate_id': candidate_id,
        })

        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        :param block: <dict> Block
        :return: <str>
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def chain_valid(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: <list> A blockchain
        :return: <bool> True if valid, False if not
        """

        previous_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{previous_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(previous_block):
                return False

            previous_block = block
            current_index += 1

        return True
