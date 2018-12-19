import base58
from ecdsa import SigningKey, SECP256k1

sk = SigningKey.from_string(base58.b58decode(open("private", 'r').read()), curve=SECP256k1)
message = open("message","rb").read()
sig = sk.sign(message)
open("signature","wb").write(sig)
