import base58
from ecdsa import VerifyingKey, BadSignatureError, SECP256k1

vk = VerifyingKey.from_string(base58.b58decode(open("public").read()), curve=SECP256k1)
message = open("message","rb").read()
sig = open("signature","rb").read()
try:
    vk.verify(sig, message)
    print("good signature")
except BadSignatureError:
    print("BAD SIGNATURE")
