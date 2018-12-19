#!/usr/bin/python
import base58
from ecdsa import VerifyingKey, SigningKey, SECP256k1
import requests
from urllib.parse import urlparse

sk = SigningKey.from_string(base58.b58decode(open("private", 'r').read()), curve=SECP256k1)
print('\n')
recipient = input('Input recipient public key: ')
print('\n')
amount = input('Amount: ')
print('\n')
nonce = input('Unique identifier: ')
print('\n')
sender = open('public', 'r').read()
address = input('Input node to send transaction to: ')
print('\n')
if not 'http' in address:
    address = 'http://' + address
node = urlparse(address).netloc
message = sender + recipient + amount + nonce
message = str.encode(message)
sig = sk.sign(message)
sig = base58.b58encode(sig)
json = {
        'sender': sender,
        'amount': amount,
        'signature': sig,
        'recipient': recipient,
        'nonce': nonce,
        }
response = requests.post(f'http://{node}/transactions/new_external', timeout=4.3, json=json)
print(response.json()['message'])
