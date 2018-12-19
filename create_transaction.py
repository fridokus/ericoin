import base58
from ecdsa import VerifyingKey, SigningKey, SECP256k1

sk = SigningKey.from_string(base58.b58decode(open("private", 'r').read()), curve=SECP256k1)
recipient = input('Input recipient public key: ')
amount = input('Amount: ')
nonce = input('Unique identifier: ')
sender = open('public', 'r').read()
message = sender + recipient + amount + nonce
message = str.encode(message)
sig = sk.sign(message)
sig = base58.b58encode(sig)
with open("transaction_info.txt","w") as f:
    f.write("Amount: "+str(amount)+"\n")
    f.write("Message (nonce): "+str(nonce)+"\n")
    f.write("Recipient: "+str(recipient)+"\n")
    f.write("Sender: "+str(sender)+"\n")
    f.write("Signature: "+str(sig)+"\n")
open("signature","w").write(sig)
print('Transaction signature in ./signature')
