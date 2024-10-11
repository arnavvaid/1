# Code by Group UG40:
# Nathan Dang (a1794954@adelaide.edu.au)
# Haydn Gaetdke (a1860571@adelaide.edu.au)
# Quoc Khanh Duong (a1872857@adelaide.edu.au)
# Dang Hoan Nguyen (a1830595@adelaide.edu.au)

from Cryptodome.Signature import pss
from Cryptodome.Hash import SHA256
from Cryptodome.PublicKey import RSA


PEM_HEADER_PUBK = "-----BEGIN PUBLIC KEY-----"
PEM_FOOTER_PUBK = "-----END PUBLIC KEY-----"


def rsaSign(message):
    with open("./private_key.pem","rb") as private_file:
        private_key = RSA.import_key(private_file.read(),passphrase="G40")
    hash = SHA256.new(message.encode("utf-8"))
    try:
        signature = pss.new(private_key, salt_bytes=32).sign(hash)
    except (ValueError):
        raise ValueError("Invalid RSA key length")
    except (TypeError):
        raise TypeError("Key has no private half")

    return signature


def rsaVerify(message, signature, pub_key):
    hash = SHA256.new(message.encode("utf-8"))
    if (pub_key.find(PEM_FOOTER_PUBK) == -1 or pub_key.find(PEM_HEADER_PUBK) == -1):
        pub_key = pub_key.replace(PEM_FOOTER_PUBK,"").replace(PEM_HEADER_PUBK,"").strip()
        pub_key = PEM_HEADER_PUBK + '\n' + pub_key + '\n' + PEM_FOOTER_PUBK
    
    rsaKey = RSA.import_key(pub_key)
    
    verifier = pss.new(rsaKey, salt_bytes=32)
    try:
        verifier.verify(hash, signature)
        return True
    except (ValueError):
        raise ValueError("Invalid signature")


if __name__ == "__main__":
    signature = rsaSign("hello")
    with open("public_key.pem", "r") as f:
        pub_k = f.read()
        
    if (rsaVerify("hello", signature, pub_k)):
        print("verified")
