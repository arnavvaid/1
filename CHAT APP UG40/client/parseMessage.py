# Code by Group UG40:
# Nathan Dang (a1794954@adelaide.edu.au)
# Haydn Gaetdke (a1860571@adelaide.edu.au)
# Quoc Khanh Duong (a1872857@adelaide.edu.au)
# Dang Hoan Nguyen (a1830595@adelaide.edu.au)

import json
import hashlib
from base64 import b64encode, b64decode
from messageEncoder import encryptMessage, decryptMessage
from rsaSigner import rsaSign, rsaVerify 
from faker import Faker



SIGNATURE = ""
PUBLIC_KEY = ""
PRIVATE_KEY = ""
FINGERPRINT = ""


PEM_HEADER_PUBK = "-----BEGIN PUBLIC KEY-----"
PEM_FOOTER_PUBK = "-----END PUBLIC KEY-----"


def PreProcessingOutMessage ():
    pass

# Take plain message as the input
def ParseOutMessage (message, msg_type, subtype, receiver, online_users):
    global PUBLIC_KEY
    global FINGERPRINT

    parsedMessage = {}
    parsedMessage['type'] = msg_type

    if msg_type == "signed_data":
        with open('./client_state.json', 'r') as client_state:
            state_data = json.load(client_state)
            FINGERPRINT = state_data['fingerprint']
        
        parsedMessage['data'] = {}
        parsedMessage['data']['type'] = subtype
        
        # When connecting to the server: I think this is done.
        # Load the public key.
        if subtype == "hello":
            # Parse public key and generate signature
            PUBLIC_KEY = (open("./public_key.pem", 'r').read())
            parsedMessage['data']['public_key'] = PUBLIC_KEY
            
        # No encrytion or encoding yet
        if subtype == "chat":
            parsedMessage['data']['destination_servers'] = []
            parsedMessage['data']['iv'] = ""
            parsedMessage['data']['symm_keys'] = []
            parsedMessage['data']['chat'] = {}
            
            parsedMessage['data']['chat']['participants'] = []
            
            with open("./client_state.json", 'r') as file:
                client_state = json.load(file)
                receiver.insert(0, FINGERPRINT)
                    
            pub_k_list = []
            
            for fp in receiver:
                if fp not in client_state['NS']:
                    raise ValueError("User not found")
                parsedMessage['data']['destination_servers'].append(client_state['NS'][fp]['server'])
                pub_k_list.append(client_state['NS'][fp]['public_key'])

            cipher_chat, iv, sym_key = encryptMessage(message, receiver, pub_k_list)
            parsedMessage['data']['chat'] = b64encode(cipher_chat).decode('utf8')
            parsedMessage['data']['iv'] = b64encode(iv).decode('utf8')
            parsedMessage['data']['symm_keys'] = sym_key
            
            
            
        if subtype == "public_chat":
            parsedMessage['data']['sender'] = FINGERPRINT
            parsedMessage['data']['sender'] = FINGERPRINT
            parsedMessage['data']['message'] = message
            
            
        # Random stuff for now
        parsedMessage['counter'] = state_data['counter']
        state_data['counter'] += 1
        # Need base64
        
        data_json_string = json.dumps(parsedMessage['data'])
        data_json_string += str(parsedMessage['counter'])
        SIGNATURE = rsaSign(data_json_string)
        parsedMessage['signature'] = b64encode(SIGNATURE).decode()
                
        with open('./client_state.json', 'w') as client_state_dump:
            json.dump(state_data, client_state_dump, indent=4)
            
    elif msg_type == "client_list_request":
        pass

                
    
    parsedJsonMessage = json.dumps(parsedMessage).encode('utf-8')
    
    
    return parsedJsonMessage

def ParseInMessage (message):
    print("--------------")
    print(message)
    print('-----------------')
    parsed_message = message.decode('utf-8')
    parsed_message = json.loads(parsed_message)

    msg_type = parsed_message['type']
    message_info = {}
    if parsed_message['type'] == "signed_data":
        msg_type += f"_{parsed_message['data']['type']}"
        try:
            signature = b64decode(parsed_message['signature'])
        except Exception as e:
            raise ValueError(e)
        if parsed_message['data']['type'] == "chat":
            try:
                ciphertext = b64decode(parsed_message['data']['chat'])
                iv = b64decode(parsed_message['data']['iv'])
                enc_key =  parsed_message['data']['symm_keys']
            except Exception as e:
                raise ValueError(e)
            

            try: 
                data_json_string = json.dumps(parsed_message['data'])
                data_json_string += str(parsed_message['counter'])
                chat = decryptMessage(ciphertext, iv, enc_key)
                sender_fp = chat['participants'][0]
                print(f"Sender fingerprint: {sender_fp}")
                state_data = {}
                with open('./client_state.json', 'r') as client_state:
                    state_data = json.load(client_state)
                    if sender_fp not in state_data['NS']:
                        raise ValueError("User not found")
                    pub_key = state_data['NS'][sender_fp]['public_key']
                    if (rsaVerify(data_json_string, signature, pub_key) == True):
                        print("Signature verified")
                    else:
                        raise ValueError("Invalid signature")
            
                    
                for fp in state_data['NS']:
                    if fp == chat['participants'][0]:
                        message_info['sender'] = "&lt;&lt; <span style='color:blue'>[FROM]</span> " + state_data['NS'][fp]['name']
                        message_info['color'] = state_data['NS'][fp]['color']            
                        message_info['message'] = chat['message']
            except Exception as e:
                raise ValueError(e)
            
            return message_info, msg_type
            
            
        if parsed_message['data']['type'] == "public_chat":
            data_json_string = json.dumps(parsed_message['data'])
            data_json_string += str(parsed_message['counter'])
            sender_fp = parsed_message['data']['sender']
            with open('./client_state.json', 'r') as client_state:
                state_data = json.load(client_state)
                if sender_fp not in state_data['NS']:
                    raise ValueError("User not found")
                pub_key = state_data['NS'][sender_fp]['public_key']
                if (rsaVerify(data_json_string, signature, pub_key) == True):
                    print("Signature verified")
                else:
                    raise ValueError("Invalid signature")
            message_info['sender'] = "&lt;&lt; <span style='color:red'>[PUBLIC CHAT]</span> <span style='color:blue'>[FROM]</span> " + state_data['NS'][sender_fp]['name']
            message_info['color'] = state_data['NS'][sender_fp]['color']            
            message_info['message'] = parsed_message['data']['message']                  
        
            return message_info, msg_type

    
    if parsed_message['type'] == "client_list":
        with open("client_state.json","r") as client_state_json:
            client_state = json.load(client_state_json)
        
        
        client_state['online_users'] = parsed_message['servers']
        
        
        for client in client_state['online_users']:
            for pub_k in client['clients']:
                
                print(pub_k)
                fp = hashlib.sha256(pub_k.encode()).hexdigest()
                if fp not in client_state['NS']:
                    client_state['NS'][fp] ={}
                    client_state['NS'][fp]['name'] = Faker().name()
                    client_state['NS'][fp]['color'] = Faker().hex_color()
                    client_state['NS'][fp]['public_key'] = pub_k
                    client_state['NS'][fp]['server'] = client['address']
                            
            with open('./client_state.json', 'w') as fout:
                json.dump(client_state, fout, indent=4)

    # return parsed_message, msg_type
    return parsed_message, msg_type
