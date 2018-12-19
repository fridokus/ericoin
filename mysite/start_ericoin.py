import os
import requests
import sys
import time

from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('-r', '--remove', action='store_true', help='Remove instead of register.')
args = parser.parse_args()
remove = args.remove


ecn = 'http://132.196.'

book_keeper = '5010'
nodes = [ecn+str(m)+'.'+str(n)+':'+book_keeper for m in (148, 157, 248, 250) for n in (23, 36, 39, 49, 81, 143, 219)]
website_port = '8001'

json = {
    'nodes': nodes,
    }

print("Please ensure that your port "+book_keeper+" is available for usage!")
# Linux OS
if os.name == "posix":
    os.chdir("/home/elanric/ml_himalaya/ericoin/")
    os.system("gnome-terminal -e 'python3 blockchain.py -p "+book_keeper+" -c 300'")
    time.sleep(15)
    os.system("gnome-terminal -e 'python3 bookkeeping.py -p "+book_keeper+" -r 1'")
    time.sleep(10)
    if not remove:
        response = requests.post("http://localhost:"+book_keeper+"/nodes/register", timeout=5, json=json)
    else:
        response = requests.post("http://localhost:"+book_keeper+"/nodes/remove", timeout=5, json=json)
    time.sleep(5)
    os.chdir("/home/elanric/ml_himalaya/ericoin/mysite")
    os.system("python3 manage.py makemigrations")
    os.system("python3 manage.py migrate")
    os.system("python3 manage.py runserver 0:"+website_port)
# Windows OS (NOT FIXED YET)
elif os.name == "nt":
    os.chdir("/home/elanric/ml_himalaya/ericoin/")
    os.system("start python blockchain.py -p "+book_keeper+" -c 100")
    time.sleep(15)
    os.system("start python bookkeeping.py -p "+book_keeper)
    time.sleep(10)
    if not remove:
        response = requests.post("http://localhost:"+book_keeper+"/nodes/register", timeout=5, json=json)
    else:
        response = requests.post("http://localhost:"+book_keeper+"/nodes/remove", timeout=5, json=json)
    time.sleep(5)
    os.chdir("/home/elanric/ml_himalaya/ericoin/mysite")
    os.system("python manage.py makemigrations")
    os.system("python manage.py migrate")
    os.system("python manage.py runserver 0:"+website_port)
# Non-compatible OS
else:
    print("What kind of a MacBook crap are you running? Switch to Linux or Windows ASAP!")
    sys.exit(0)

