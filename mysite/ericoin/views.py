import base58
import os
import requests
import subprocess
import sys
import threading
import time
import urllib

from django.http import Http404, HttpRequest, HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, render_to_response
from django.urls import reverse, reverse_lazy
from django.views import generic

from .forms import *
from .models import *

from ecdsa import VerifyingKey, SigningKey, SECP256k1
from requests import ReadTimeout, ConnectTimeout 
from requests.exceptions import ConnectionError
from urllib.parse import urlparse

ecn = '132.196.'

book_keeper = '5010'
miners = (5000, 5001)
third = (148, 157)
fourth = (39, 81)
addresses = [ecn+str(i)+'.'+str(j)+':'+str(k) for i in third for j in fourth for k in miners]

class IndexView(generic.DetailView):
    template_name = 'ericoin/index.html'
    context_object_name = 'information'
    def get_latest_block(self):
        response = requests.post('http://localhost:5010/chain_short', timeout=3, json={'start_index': -1})
        last_block = response.json()['chain'][-1]
        str_hex_target = str(hex(last_block['target']))
        last_block['target'] = '0x'+''.join(['0' for i in range(64-len(str_hex_target)+2)])+str_hex_target[2:]
        last_block['timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_block['timestamp']))
        del last_block['transactions']
        last_block = list(last_block.values())
        return last_block
    def get_object(self, queryset=None):
        return Transaction.objects.all()


class BalanceView(generic.DetailView):
    template_name = 'ericoin/balances.html'
    context_object_name = 'information'
    def get_account_balances(self):
        try:
            response = requests.get('http://localhost:5010/balances', timeout=3)
            accounts = list(response.json().keys())
            account_balances = list(response.json().values())
        except (ConnectionError, ConnectTimeout, ReadTimeout):
            accounts = []
            account_balances = []
        return [accounts, account_balances]
    def get_object(self, queryset=None):
        return Account.objects.all()


class ChainView(generic.DetailView):
    template_name = 'ericoin/blockchain.html'
    context_object_name = 'information'
    def get_block_chain(self):
        try:
            response = requests.get('http://localhost:5010/chain', timeout=5)
            chain_history = response.json()['chain']
            for c in chain_history:
                str_hex_target = str(hex(c['target']))
                c['target'] = '0x'+''.join(['0' for i in range(64-len(str_hex_target)+2)])+str_hex_target[2:]
                c['timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(c['timestamp']))
                del c['transactions']
            block_chain = [list(d.values()) for d in chain_history]
        except (ConnectionError, ConnectTimeout, ReadTimeout):
            block_chain = []
        return block_chain
    def get_object(self, queryset=None):
        return Transaction.objects.all()
        
        
class TransactionView(generic.DetailView):
    template_name = 'ericoin/transactions.html'
    context_object_name = 'information'
    def get_transaction_history(self):
        counter_b = 0
        counter_t = 0
        index_b = []
        index_t = []
        reward = []
        tmp = []
        transactions = []
        try:
            response = requests.get('http://localhost:5010/chain', timeout=5)
            chain = response.json()['chain']
            for i in range(1, len(chain)):
                counter_b += 1
                index_b.append(counter_b)
                for t in chain[i]['transactions']:
                    transactions.append(t)
                    if t['sender'] == '0':
                        index_t.append(0)
                        reward.append(1)
                    else:
                        counter_t += 1
                        index_t.append(counter_t)
                        reward.append(0)
            transactions = [list(d.values()) for d in transactions]
        except (ConnectionError, ConnectTimeout, ReadTimeout):
            pass
        return [list(reversed(index_b)), list(reversed(index_t)), list(reversed(transactions)), list(reversed(reward))]
    def make_transaction(request):
        if request.method == 'POST':
            form = TransactionForm(request.POST)
            if form.is_valid():
                print("\n\nValid\n\n")
                pass
            try:
                amount = form.cleaned_data['amount']
                message = form.cleaned_data['message']
                recipient = form.cleaned_data['recipient']
                sender = form.cleaned_data['sender']
                signature = form.cleaned_data['signature']
                status = []
                for a in addresses:
                    json = {
                            'amount': amount,
                            'nonce': message,
                            'recipient': recipient,
                            'sender': sender,
                            'signature': signature,
                            }
                    try:
                        response = requests.post(f'http://{a}/transactions/new_external', timeout=1, json=json)
                        status.append(response.json()['message'])
                    except (ConnectionError, ConnectTimeout, ReadTimeout):
                        pass
                    status = sorted(set(status))
            except KeyError:
                pass
        else:
            form = TransactionForm()
        return render(request, 'sent.html', {'form': form, 'status': status})
    def get_object(self, queryset=None):
        return Transaction.objects.all()


