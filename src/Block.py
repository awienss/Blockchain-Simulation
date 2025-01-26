# import section

import json
import hashlib
from uuid import uuid4
from time import time
from urllib.parse import urlparse
import requests
from flask import Flask, jsonify, request

# Block class

class Block:

    def __init__(self):
        self.chain = []
        self.transactions_current_state = []
        self.nodes = set()
        self.new_block(previous_hash='1', proof=100)

    def valid_chain(self, chain):

        # valis_chain checks validity of blockchain

        previous_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            
            previous_block_hash = self.hash(previous_block)
            if block['previous_hash'] != previous_block_hash:

                return False

            if not self.valid_proof(previous_block['proof'], block['proof'], previous_block_hash):

                return False

            previous_block = block
            current_index += 1

        return True

    def register_node(self, address):

        # resister_node adds a new node to the current list

        parsed_path = urlparse(address)

        if parsed_path.netloc:
            self.nodes.add(parsed_path.netloc)

        elif parsed_path.path:
            self.nodes.add(parsed_path.path)

        else:
            raise ValueError('URL is invalid')

    def resolve_conflicts(self):

        # resolve_conflicts uses consensus algorithm to ensure correct chain is used

        adjacent_nodes = self.nodes
        new_chain = None

        max_length = len(self.chain)

        for node in adjacent_nodes:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:

            self.chain = new_chain
            return True

        return False
    
    def new_transaction(self, sender, recipient, amount):

        # new_transaction creates a new transaction for next Block
        
        self.transactions_current_state.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.previous_block['index'] + 1

    def new_block(self, proof, previous_hash):

        # new_block creates a new block

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.transactions_current_state,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        self.transactions_current_state = []

        self.chain.append(block)

        return block

    @property
    def previous_block(self):

        # previous_block returns the last Block in chain

        return self.chain[-1]

    @staticmethod
    def hash(block):

        # hash creates a SHA-256 hash

        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, previous_block):

        # proof_of_work uses algorithm to find a new proof for the chain

        last_proof = previous_block['proof']

        last_hash = self.hash(previous_block)

        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):

        # valid_proof validates the proof from proof_of_work

        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def get_balance(self, address):

        # get_balance calculates the updated balance of the entered address
    
        balance = 0
        for block in self.chain:
            for transaction in block['transactions']:
                if transaction['recipient'] == address:
                    balance += transaction['amount']
                if transaction['sender'] == address:
                    balance -= transaction['amount']
        return balance
    
# various methods for interacting with the blockchain (mining, smart contract, new transactions, etc.)

app = Flask(__name__)

node_identifier = str(uuid4()).replace('-', '')

blockchain = Block()

@app.route('/mine', methods=['GET'])
def mine():
    previous_block = blockchain.previous_block
    proof = blockchain.proof_of_work(previous_block)

    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    previous_hash = blockchain.hash(previous_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route('/balance/<address>', methods=['GET'])
def get_balance(address):
    """
    Endpoint to retrieve the balance of a specific address.

    :param address: Wallet address
    :return: Balance of the address
    """
    balance = blockchain.get_balance(address)
    response = {
        'address': address,
        'balance': balance
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: INVALID. Supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added to the chain',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Replaced chain',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is sound',
            'chain': blockchain.chain
        }

    return jsonify(response), 200

@app.route('/smart-contract', methods=['GET'])
def simple_smart_contract():
    """
    A simple smart contract that checks if total balance exceeds 10.
    """
    total_balance = sum(tx['amount'] for block in blockchain.chain for tx in block['transactions'])

    if total_balance > 10:
        response = {
            'message': 'Smart Contract Executed',
            'condition': 'Total balance > 10',
            'action': 'Reward user with bonus',
            'status': 'Condition Met'
        }
    else:
        response = {
            'message': 'Smart Contract Executed',
            'condition': 'Total balance > 10',
            'action': 'No reward given',
            'status': 'Condition Not Met'
        }

    return jsonify(response), 200

if __name__ == '__main__':

    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=1000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port)