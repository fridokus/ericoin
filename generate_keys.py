import base58
from ecdsa import SigningKey, SECP256k1
from ecdsa import VerifyingKey
from ecdsa.util import randrange_from_seed__trytryagain

def make_key_from_seed(seed, curve=SECP256k1):
    secexp = randrange_from_seed__trytryagain(seed, curve.order)
    return SigningKey.from_secret_exponent(secexp, curve)

seed = input("Type a seed, the longer the better")
sk = make_key_from_seed(seed)
vk = sk.get_verifying_key()
# vk_pem = vk.to_pem()
# vk_pem = vk_pem[27:-26]
# vk_pem = vk_pem[:64] + vk_pem[65:]
open("private","w").write(base58.b58encode(sk.to_string()))
open("public","w").write(base58.b58encode(vk.to_string()))

print('Private key stored in ./private, public key in ./public.')
