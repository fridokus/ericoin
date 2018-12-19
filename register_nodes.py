from argparse import ArgumentParser
import requests

parser = ArgumentParser()
parser.add_argument('-r', '--remove', action='store_true', help='Remove instead of register.')
args = parser.parse_args()
remove = args.remove

node = input('Input IP of node: ')
port = input('Input port of node: ')
local_port = input('Input port of local node to send this instruction to: ')

json = {
        'nodes': ['http://%s:%s' % (node, port)], 
        }

if not remove:
    response = requests.post('http://localhost:%s/nodes/register' % local_port, timeout=2.3, json=json)
else:
    response = requests.post('http://localhost:%s/nodes/remove' % local_port, timeout=2.3, json=json)


print(response.json()['message'])
print('Nodes: ' + str(response.json()['nodes']))
print('Broadcast nodes: ' + str(response.json()['broadcast_nodes']))
