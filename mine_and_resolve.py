from argparse import ArgumentParser
import requests
from requests import ReadTimeout
from time import sleep, time, localtime, strftime

parser = ArgumentParser()
parser.add_argument('-p', '--port', default=5000, type=int, help='port to act on')
args = parser.parse_args()
port = args.port

host = 'http://localhost:' + str(port)

print('Mining on %s.' % host)

while 1:
    timeout = 2
    try:
        command = '/nodes/resolve'
        response_resolve = requests.get(host + command, timeout=timeout)
    except ReadTimeout:
        now = strftime("%Y-%m-%d %H:%M:%S", localtime())
        print(now + ': No response for %d seconds when trying %s.' % (timeout, command))
        pass
    sleep(.01)

    timeout = 3
    try:
        command = '/mine'
        response_mine = requests.get(host + command, timeout=timeout)
    except ReadTimeout:
        now = strftime("%Y-%m-%d %H:%M:%S", localtime())
        print(now + ': No response for %d seconds when trying %s.' % (timeout, command))
        pass
    sleep(.01)
