#!/usr/bin/python
import requests
import os
import time

os.system('start python blockchain.py')
os.system('start python blockchain.py -p 5001')
os.system('start python blockchain.py -p 5010 -c 100')

sleep = 5
print('Started 2 mining nodes at ports 5000 and 5001 and 1 bookkeeping node at port 5010. Sleeping for %d seconds.' % sleep)
time.sleep(sleep)

json = {
        'nodes': ['http://localhost:5010'], 
        'broadcast_nodes': ['http://localhost:5010']
        }

response = requests.post(f'http://localhost:5000/nodes/register', timeout=2.3, json=json)
response = requests.post(f'http://localhost:5001/nodes/register', timeout=2.3, json=json)

print('Registred bookkeeping node in miners.')
time.sleep(1)

os.system('start python mine_and_resolve.py')
os.system('start python mine_and_resolve.py -p 5001')
os.system('start python bookkeeping.py -p 5010')

print('Started mining and bookkeeping scripts.')
