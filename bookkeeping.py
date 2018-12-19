from requests import ReadTimeout, ConnectTimeout
from argparse import ArgumentParser
import requests
from requests import ReadTimeout
from time import sleep, time, localtime, strftime

def now():
    return strftime("%Y-%m-%d %H:%M:%S", localtime())
def nowprint(message):
    print(now() + ': ' + message)

parser = ArgumentParser()
parser.add_argument('-p', '--port', default=5000, type=int, help='port to act on')
parser.add_argument('-r', '--refresh', default=4, type=int, help='refresh interval')
args = parser.parse_args()
port = args.port
refresh = args.refresh
save_interval = 60 
next_save = time() + 2

host = 'http://localhost:' + str(port)

nowprint('Bookkeeping on %s.' % host)

try:
    response = requests.get(host + '/load')
    nowprint(response.json()['message'])
except:
    nowprint('Blockchain loading failed')
    pass

while 1:
    timeout = 2
    try:
        command = '/nodes/resolve'
        response_resolve = requests.get(host + command, timeout=timeout)
    except ReadTimeout:
        nowprint('No response for %d seconds when trying %s.' % (timeout, command))
        pass
    if time() > next_save:
        try:
            command = '/save'
            response_save = requests.get(host + command, timeout=timeout)
            nowprint(response_save.json()['message'])
            next_save = time() + save_interval * 60
        except ReadTimeout:
            nowprint('No response for %d seconds when trying %s.' % (timeout, command))
            pass
    sleep(refresh)
