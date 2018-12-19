#!/usr/bin/python
import base58
import copy
from ecdsa import SigningKey, VerifyingKey, BadSignatureError, SECP256k1
import hashlib
import json
import random
import socket
import sys
from time import time
from urllib.parse import urlparse
from uuid import uuid4

import requests
from requests import ReadTimeout, ConnectTimeout 
from requests.exceptions import ConnectionError
from flask import Flask, jsonify, request


class Blockchain:
    def __init__(self):
        self.addresses = set()
        self.block_time = 300
        self.blocks_per_adjust = 30
        self.broadcast_nodes = set()
        self.current_transactions = []
        self.chain = []
        self.cooldown_time = 0
        self.cooldowns = dict()
        self.hashed_transactions = []
        self.ip = socket.gethostbyname(socket.gethostname())
        self.nodes = set()
        self.port = 0
        self.short_chain_len = 5
        self.target = '00000' + ''.join(['e' for i in range(64 - 5)])
        self.target_int = int(self.target, 16)
        self.transaction_hashes = set()
        self.transaction_hashes_last_index = 0

        self.print_target(self.target_int)
        self.new_block(previous_hash='elanric_ezfrios', nonce=int('ericsson', 36), genesis=True)
        self.mining_reward(public_key)

    def remove_broadcast_node(self, address):
        parsed_url = urlparse(address)
        try:
            self.broadcast_nodes.remove(parsed_url.netloc)
        except KeyError as e:
            print('Node %s not found in set of broadcast nodes.' % parsed_url.netloc)
            return False
        return True

    def remove_node(self, address):
        parsed_url = urlparse(address)
        try:
            self.nodes.remove(parsed_url.netloc)
        except KeyError as e:
            print('Node %s not found in set of nodes.' % parsed_url.netloc)
            return False
        return True
    
    def register_broadcast_node(self, address):
        parsed_url = urlparse(address)
        self.broadcast_nodes.add(parsed_url.netloc)

    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
        self.cooldowns[parsed_url.netloc] = 0

    def register_address(self, address):

        self.addresses.add(address)

    def valid_chain(self, chain, start_index=0):
        if start_index > 0:
            current_index = start_index
        else:
            current_index = 1
        last_block = chain[current_index - 1]
        while current_index < len(chain):
            block = chain[current_index]
            sys.stdout.write("\rChecking validity of block " + str(block['index']) + '.')
            sys.stdout.flush()
            for transaction in block['transactions']:
                if transaction['sender'] is not '0':
                    if transaction['hash'] in self.transaction_hashes:
                        print('\nHash of a transaction was found in current blockchain')
                if transaction['amount'] < 0:
                    print('\nAmount in a transaction was < 0')
                    return False
            if block['previous_hash'] != self.hash(last_block):
                print('\nPrevious hash in block %d not equal to hash of block %d.' % (current_index, current_index - 1))
                return False
            info = self.hash(block['transactions']) + block['previous_hash'] + str('%d' % last_block['nonce'])
            if not self.valid_proof(info, block['nonce'], block['target']):
                print('\nBlock %d invalid.' % block['index'])
                return False
            last_block = block
            current_index += 1
        print('\n')
        return True

    def replace_chain(self, max_length, node):
        new_chain = None
        try:
            response = requests.post(f'http://{node}/chain_short', timeout=0.3, json={'start_index': max_length})
            if response.status_code == 200:
                length = response.json()['length']
                chain_short = response.json()['chain']
                if length > len(self.chain):
                    chain_short_start = chain_short[0]['index'] - 1
                    chain = self.chain[:chain_short_start] + chain_short
                    if self.valid_chain(chain, start_index=chain_short_start):
                        print('\nReplaced %d last blocks using chain_short.' % (length - max_length))
                        max_length = length
                        new_chain = chain
                        for block in chain_short:
                            for transaction in block['transactions']:
                                if transaction['sender'] is not '0':
                                    self.transaction_hashes.add(transaction['hash'])
                                    for current_transaction in self.current_transactions:
                                        if transaction['hash'] == current_transaction['hash']:
                                            self.current_transactions.remove(current_transaction)
                                            print('\nRemoved transaction with nonce %s from queue.' % \
                                                    transaction['nonce'])
                                            if current_transaction in self.hashed_transactions:
                                                self.hashed_transactions.remove(current_transaction)
                    elif max_length >= 8:
                        print('\nShort chain not valid, attempting to get longer chain.')
                        new_chain = self.replace_chain(max_length - 5, node)
                    else:
                        print('\nShort chain not valid, attempting to get entire chain.')
                        try:
                            response_2 = requests.get(f'http://{node}/chain', timeout=6)
                            if response_2.status_code == 200:
                                length = response_2.json()['length']
                                chain = response_2.json()['chain']
                                if self.valid_chain(chain):
                                    print('\nReplaced entire chain using chain.')
                                    max_length = length
                                    new_chain = chain
                        except (ReadTimeout, ConnectTimeout) as e:
                            print('Timeout when trying to get entire chain from %s.' % node)
                            pass
        except (ReadTimeout, ConnectTimeout) as e:
            print('Timeout when trying to get short chain from %s.' % node)
            print('Node %s put on cooldown for %d minutes.' % (node, int(self.cooldown_time / 60)))
            self.cooldowns[node] = time() + self.cooldown_time
            pass
        except ConnectionError as e:
            print('Connection error to node %s.' % node)
            print('Node %s put on cooldown for %d minutes.' % (node, int(self.cooldown_time / 60)))
            self.cooldowns[node] = time() + self.cooldown_time
            pass
        return new_chain

    def update_target(self):
        if self.target_int != self.chain[-1]['target']:
            self.target_int = self.chain[-1]['target']
            self.print_target(self.target_int)
            print('Target updated from last block.')
        elif not self.chain[-1]['index'] % self.blocks_per_adjust:
            reference_index = self.chain[-1]['index'] - self.blocks_per_adjust
            if self.chain[-1]['index'] == self.blocks_per_adjust:
                reference_index += 1
            self.calculate_new_target(reference_index)
            self.print_target(self.target_int)
            print('Target updated from calculation.')

    def resolve_conflicts(self):
        neighbours = self.nodes
        max_length = len(self.chain)
        for node in neighbours:
            if not('localhost:' + str(self.port) in node or self.ip in node) and\
                    self.cooldowns[node] < time():
                new_chain = self.replace_chain(max_length, node)
                if new_chain:
                    self.chain = new_chain
                    self.update_target()
                    return True
        return False

    def calculate_new_target(self, reference_index):
        now = self.chain[-1]['timestamp']
        then = self.chain[reference_index]['timestamp']
        adjustment_factor = (now - then) / self.blocks_per_adjust / self.block_time
        self.target_int = int(self.target_int * adjustment_factor)

    def new_block(self, nonce, previous_hash, genesis=False):
        new_index = len(self.chain) + 1
        block = {
            'index': new_index,
            'timestamp': time() if not genesis else 6215,
            'transactions': self.hashed_transactions,
            'nonce': nonce,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
            'target': self.target_int,
        }
        for node in self.broadcast_nodes:
            response = requests.post(f'http://{node}/append_block', timeout=2, json={'block': block})
            if response.status_code == 200:
                print('Block with index %d successfully broadcasted to %s.' % (new_index, node))
            elif response.status_code == 400:
                print('Block with index %d deemed as invalid by %s. Replacing chain.' % (new_index, node))
                self.replace_chain(new_index - 1, node)
                return None
            elif response.status_code == 401:
                print('Block with index %d too short for %s. Replacing chain.' % (new_index, node))
                self.replace_chain(new_index - 1, node)
                return None
            else:
                print('Error.')
                print(response)
        self.chain.append(block)
        self.update_target()
        self.current_transactions = [i for i in self.current_transactions if not i in self.hashed_transactions]
        self.hashed_transactions = []
        self.mining_reward(public_key)
        return block

    def calculate_balances(self):
        balances = dict()
        for block in self.chain:
            for transaction in block['transactions']:
                if not transaction['sender'] in self.addresses:
                    self.register_address(transaction['sender'])
                if not transaction['recipient'] in self.addresses:
                    self.register_address(transaction['recipient'])
        for address in self.addresses:
            balances[address] = 0
        for block in self.chain:
            for transaction in block['transactions']:
                balances[transaction['sender']] -= int(transaction['amount'])
                balances[transaction['recipient']] += int(transaction['amount'])
        return balances


    def sign_message(self, private_key, message):
        sk = SigningKey.from_string(private_key, curve=SECP256k1)
        sig = sk.sign(message)
        return sig

    def mining_reward(self, recipient):
        if not any(transaction['sender'] == '0' for transaction in self.current_transactions):
            transaction = {
                'sender': '0',
                'recipient': recipient,
                'amount': 10,
                'sig_base58': recipient,
                'nonce': base58.b58encode(str(random.randint(1, 1e50)).encode()),
            }
            transaction['hash'] = self.hash_transaction(transaction)
            self.current_transactions.append(transaction)

    def new_transaction(self, private_key=None, sender=None, recipient=None, amount=None, sig=None, nonce=None):
        if int(amount) < 0:
            return -3
        message = str.encode(sender + recipient + str(amount) + nonce)
        if sig:
            sig = base58.b58decode(sig)
        if private_key:
            sig = self.sign_message(private_key=private_key, message=message)
        try:
            vk = VerifyingKey.from_string(base58.b58decode(sender), curve=SECP256k1)
        except (AssertionError, ValueError) as e:
            print('Bad address')
            return -1
        try:
            vk.verify(sig, message)
            print("good signature")
        except BadSignatureError:
            print("BAD SIGNATURE")
            return -2
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': int(amount),
            'sig_base58': base58.b58encode(sig),
            'nonce': nonce,
        }
        transaction['hash'] = self.hash_transaction(transaction)
        self.update_transaction_hashes()
        if transaction['hash'] not in self.transaction_hashes:
            self.current_transactions.append(transaction)
            return self.last_block['index'] + 1
        return -4

    def update_transaction_hashes(self):
        for block in self.chain[self.transaction_hashes_last_index:]:
            for transaction in block['transactions']:
                if transaction['sender'] is not '0':
                    self.transaction_hashes.add(self.hash_transaction(transaction))
        self.transaction_hashes_last_index = len(self.chain) - 1

    @property
    def last_block(self):
        return self.chain[-1]

    def hash_transaction(self, transaction):
        transaction_nohash = {
                'sender': transaction['sender'],
                'recipient': transaction['recipient'],
                'amount': int(transaction['amount']),
                'nonce': transaction['nonce'],
                }
        return self.hash(transaction_nohash)


    def print_target(self, target_int):
        str_hex_target = str(hex(target_int))
        target_str = '0x' + ''.join(['0' for i in range(64 - len(str_hex_target) + 2)]) + str_hex_target[2:]
        print('Target: %s\n' % target_str)

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_nonce, previous_hash, recheck_time):
        nonce = random.randint(0, 1e40)
        target_int = self.target_int
        limit = time() + recheck_time
        self.hashed_transactions = copy.deepcopy(self.current_transactions)
        info = self.hash(self.hashed_transactions) + previous_hash + str('%d' % last_nonce)
        while not self.valid_proof(info, nonce, target_int):
            nonce += 1
            if (not nonce % 100) and (time() > limit):
                nonce = -1
                break
        return nonce

    @staticmethod
    def valid_proof(info, nonce, target_int):
        guess = f'{info}{nonce}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return int(guess_hash, 16) < target_int


app = Flask(__name__)
public_key = open("public").read()
blockchain = Blockchain()
blockchain.register_address(public_key)


@app.route('/mine', methods=['GET'])
def mine():
    '''
    Sending this command to the node will make the node try to find a block 
    during 1 second (recheck_time). The hash of the block that it's trying to find has to
    be less than target_int. 
    '''
    recheck_time = 1
    last_block = blockchain.last_block
    last_nonce = last_block['nonce']
    previous_hash = blockchain.hash(last_block)
    nonce = blockchain.proof_of_work(last_nonce, previous_hash, recheck_time)
    # If a block is found then the nonce returned by proof_of_work will be positive.
    if nonce >= 0:
        block = blockchain.new_block(nonce, previous_hash)
        # If None is returned then the block was rejected by one of the nodes in broadcast_nodes.
        if not block is None:
            response = {
                'message': "New block forged",
                'index': block['index'],
                'transactions': block['transactions'],
                'nonce': block['nonce'],
                'previous_hash': block['previous_hash'],
            }
            response_value = 200
            print('Block %d found!' % block['index'])
        else:
            response = {
                    'message': 'Block rejected by a broadcast node.',
                    }
            response_value = 401
    else:
        response = {
                'message': 'No block found in %.2f seconds' % recheck_time,
                }
        response_value = 400
    return jsonify(response), response_value


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    '''
    Generate a new transaction using the private key in the same folder as
    blockchain.py. The sender has to be the corresponding public key, i.e. 
    the public key found in ./public.
    '''
    values = request.get_json()
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400
    if values['amount'] < 0:
        return 'Amount < 0', 400
    try:
        if values['nonce']:
            pass
    except KeyError:
        values['nonce'] = random.randint(1, 1e30)
        pass
    if not values['recipient'] in blockchain.addresses:
        blockchain.register_address(values['recipient'])
    private_key = base58.b58decode(open("private").read())
    index = blockchain.new_transaction(private_key, sender=values['sender'],\
            recipient=values['recipient'], amount=values['amount'], nonce=values['nonce'])
    # index is current block index + 1
    # Negative values are used as error codes
    if index == -1:
        response = {'message': 'Bad address.'}
    elif index == -2:
        response = {'message': 'Bad signature.'}
    elif index == -3:
        response = {'message': 'Amount < 0.'}
    elif index == -4:
        response = {'message': 'Hash of transaction already found in blockchain.'}
    else:
        response = {'message': 'Transaction will be added to the next block mined.'}
    return jsonify(response), 201


@app.route('/check_validity', methods=['GET'])
def check_validity():
    '''
    If this returns False there is something wrong with the script.
    '''
    response = {
            'valid_chain': blockchain.valid_chain(blockchain.chain),
            'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/balances', methods=['GET'])
def balances():
    response = blockchain.calculate_balances()
    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/chain_short', methods=['POST'])
def short_chain():
    '''
    Returns chain from index specified in start_index.
    '''
    values = request.get_json()
    required = ['start_index']
    if not all(k in values for k in required):
        return 'Missing length', 400

    start_index = values['start_index']
    response = {
            'chain': blockchain.chain[start_index - 1:],
            'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/length', methods=['GET'])
def get_length():
    response = {
            'length': len(blockchain.chain),
            }
    return jsonify(response), 200


@app.route('/nodes_broadcast/register', methods=['POST'])
def register_broadcast_node():
    '''
    A broadcast_node is a node to which this node will attempt to broadcast all
    blocks mined. They will be accepted by the receiving node if they fit on
    top of the chain that node already has. Ideally, you want to run a node using
    bookkeeping.py and adding that node as a broadcast_node in your mining nodes.
    This setup is described in README.md of this gerrit project.
    '''
    values = request.get_json()
    nodes = values.get('nodes')
    success = False
    if nodes is None:
        return "Error: Please supply a valid list of nodes.", 400
    for node in nodes:
        result = blockchain.register_broadcast_node(node)
        if result:
            success = True
    response = {
        'message': 'Broadcast nodes have been added.',
        'broadcast_nodes': list(blockchain.broadcast_nodes),
    }
    return jsonify(response), 201


@app.route('/append_block', methods=['POST'])
def append_block():
    '''
    The method used by mining nodes to attempt to broadcast a block found 
    to this node.
    '''
    values = request.get_json()
    if not 'block' in values:
        return 'Missing block', 402
    index = values['block']['index']
    if index > blockchain.chain[-1]['index']:
        if blockchain.valid_chain(blockchain.chain + [values['block']], start_index=index - 2):
            blockchain.chain.append(values['block'])
            for transaction in values['block']['transactions']:
                if transaction['sender'] is not '0':
                    blockchain.transaction_hashes.add(transaction['hash'])
            response = {
                    'message': 'Block with index %d was added to the chain.' % index,
                    }
            blockchain.update_target()
            status_code = 200
        else:
            response = {
                    'message': 'Block with index %d invalid for this chain of length %d.'\
                            % (index, len(blockchain.chain)),
                            }
            status_code = 400
    else:
        response = {
                'message': 'This chain is already as long or longer.',
                }
        status_code = 401
    return jsonify(response), status_code
        

@app.route('/nodes/remove', methods=['POST'])
def remove_nodes():
    '''
    Remove nodes from which this node requests chain_short and chain.
    Removing nodes that are offline could be desireable.
    '''
    values = request.get_json()
    nodes = values.get('nodes')
    broadcast_nodes = values.get('broadcast_nodes')
    success = False
    if not nodes is None:
        for node in nodes:
            result = blockchain.remove_node(node)
            if result:
                success = True
    if not broadcast_nodes is None:
        for node in broadcast_nodes:
            result = blockchain.remove_broadcast_node(node)
            if result:
                success = True
    response = {
        'message': 'Nodes have been removed.' if success else \
                'Some node in the list provided was not found in set',
        'nodes': list(blockchain.nodes),
        'broadcast_nodes': list(blockchain.broadcast_nodes),
    }
    return jsonify(response), 201

@app.route('/transactions/new_external', methods=['POST'])
def external_transaction():
    '''
    Used by sign_and_send_transaction.py. Doesn't require a private key but
    just a signature, making it a safe option to broadcast transactions
    to other nodes.
    '''
    values = request.get_json()
    required = ['sender', 'recipient', 'amount', 'signature']
    if not all(k in values for k in required):
        return 'Missing values', 400
    if not values['recipient'] in blockchain.addresses:
        blockchain.register_address(values['recipient'])
    try:
        if values['nonce']:
            pass
    except KeyError:
        values['nonce'] = str(random.randint(1, 1e30))
        pass 
    index = blockchain.new_transaction(sender=values['sender'], recipient=values['recipient'],\
            amount=values['amount'], sig=values['signature'], nonce=values['nonce'])
    if index == -1:
        response = {'message': 'Bad address.'}
    elif index == -2:
        response = {'message': 'Bad signature.'}
    elif index == -3:
        response = {'message': 'Amount < 0'}
    elif index == -4:
        response = {'message': 'Hash of transaction already found in blockchain.'}
    else:
        response = {'message': 'Transaction will be added to the next block mined.'}
    return jsonify(response), 201

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    '''
    Register nodes, from which to request chain_short and chain, and broadcast_nodes,
    to which this node will attempt to broadcast a block if a block is mined.
    '''
    values = request.get_json()
    nodes = values.get('nodes')
    broadcast_nodes = values.get('broadcast_nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes.", 400
    for node in nodes:
        blockchain.register_node(node)
    if not broadcast_nodes is None:
        for node in broadcast_nodes:
            result = blockchain.register_broadcast_node(node)
    response = {
        'message': 'New nodes have been added.',
        'nodes': list(blockchain.nodes),
        'broadcast_nodes': list(blockchain.broadcast_nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    '''
    Will look through nodes in "nodes" to acquire the longest valid chain.
    '''
    replaced = blockchain.resolve_conflicts()
    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }
    return jsonify(response), 200


@app.route('/save', methods=['GET'])
def save_chain():
    '''
    Saves the blockchain to blockchain.json
    '''
    try:
        with open('blockchain.json', 'w') as f:
            json.dump(blockchain.chain, f)
        response = {
                'message': 'Blockchain saved to blockchain.json'
                }
    except:
        response = {
                'message': 'Blockchain not saved'
                }
        return jsonify(response), 400
    return jsonify(response), 200


@app.route('/load', methods=['GET'])
def load_chain():
    '''
    Loads the blockchain from blockchain.json
    '''
    try:
        with open('blockchain.json', 'r') as f:
            blockchain.chain = json.load(f)
        response = {
                'message': 'Blockchain loaded from blockchain.json'
                }
    except:
        response = {
                'message': 'Blockchain not loaded'
                }
        return jsonify(response), 400
    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    parser.add_argument('-c', '--cooldown', default=60 * 20, type=int, help='cooldown for unreachable nodes')
    args = parser.parse_args()
    port = args.port
    cooldown = args.cooldown
    blockchain.port = port
    blockchain.cooldown_time = cooldown

    app.run(host='0.0.0.0', port=port)

