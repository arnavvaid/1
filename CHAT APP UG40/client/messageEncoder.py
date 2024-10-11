# Code by Group UG40:
# Nathan Dang (a1794954@adelaide.edu.au)
# Haydn Gaetdke (a1860571@adelaide.edu.au)
# Quoc Khanh Duong (a1872857@adelaide.edu.au)
# Dang Hoan Nguyen (a1830595@adelaide.edu.au)

from Cryptodome.Cipher import AES, PKCS1_OAEP
from Cryptodome.Random import get_random_bytes
from Cryptodome.PublicKey import RSA
from Cryptodome.Hash import SHA256
from base64 import b64encode, b64decode
import json
from hex_to_bin import hex_to_bin

IV_LENGTH = 16
KEY_LENGTH = 16

PEM_HEADER_PUBK = "-----BEGIN PUBLIC KEY-----"
PEM_FOOTER_PUBK = "-----END PUBLIC KEY-----"

def encryptMessage(plaintext, participants, pub_keys):
    
    chat = {}
    chat['participants'] = []
    chat['message'] = plaintext
    
    for participant in participants:
        chat['participants'].append(b64encode(participant.encode()).decode('utf-8'))
    
    chat = json.dumps(chat).encode('utf-8')
    

    iv = get_random_bytes(IV_LENGTH)
    
    sym_key = get_random_bytes(KEY_LENGTH)
    
    cipher_aes = AES.new(sym_key, AES.MODE_GCM, iv)
    cipher_chat, authTag = cipher_aes.encrypt_and_digest(chat)
    returned_cipher = cipher_chat + authTag
    # print(returned_cipher)
    
    symm_keys = []
    
    for pub_key in pub_keys:
        if (pub_key.find(PEM_FOOTER_PUBK) == -1 or pub_key.find(PEM_HEADER_PUBK) == -1):
            pub_key = pub_key.replace(PEM_FOOTER_PUBK,"").replace(PEM_HEADER_PUBK,"").strip()
            pub_key = PEM_HEADER_PUBK + '\n' + pub_key + '\n' + PEM_FOOTER_PUBK
         
        rsa_public = RSA.import_key(pub_key)
        cipher_rsa = PKCS1_OAEP.new(rsa_public, SHA256)
        enc_key = cipher_rsa.encrypt(sym_key)
        encoded_enc_key = b64encode(enc_key).decode('utf8')
        symm_keys.append(encoded_enc_key)

    
    
    return(returned_cipher, iv, symm_keys)

def decryptMessage(ciphertext, iv, enc_sym_keys):
    with open("./private_key.pem","r") as private_file:
        private_key = RSA.import_key(private_file.read(), passphrase="G40")
    
    decoded_enc_keys = [b64decode(key) for key in enc_sym_keys]
    cipher_rsa = PKCS1_OAEP.new(private_key, SHA256)
    auth_tag_len = 16 #16 bytes
    auth_tag = ciphertext[-auth_tag_len:]
    ciphertext = ciphertext[:-auth_tag_len]
    for enc_sym_key in decoded_enc_keys:
        try:
            decrypted_sym_key = cipher_rsa.decrypt(enc_sym_key)
            break
        except:
            continue
    try:
        cipher = AES.new(decrypted_sym_key, AES.MODE_GCM, iv)
        chat = cipher.decrypt_and_verify(ciphertext,auth_tag)
        chat = json.loads(chat.decode('utf-8'))
        for i in range(len(chat['participants'])):
            decoded = b64decode(chat['participants'][i].encode('utf8'))
            try: 
                hex = decoded.decode('utf8')
                chat['participants'][i] = hex_to_bin(hex)
            except UnicodeDecodeError:
                chat['participants'][i] = hex_to_bin(decoded)
    except:
        return False
    return chat


