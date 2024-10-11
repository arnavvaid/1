# Code by Group UG40:
# Nathan Dang (a1794954@adelaide.edu.au)
# Haydn Gaetdke (a1860571@adelaide.edu.au)
# Quoc Khanh Duong (a1872857@adelaide.edu.au)
# Dang Hoan Nguyen (a1830595@adelaide.edu.au)

from binascii import hexlify

def hex_to_bin(data):
    if isinstance(data, bytes):
            assert len(data) == 32
            hexdigest = hexlify(data).decode()
            return hexdigest
    elif isinstance(data, str):
        assert len(data) == 64
        try:
            int(data, 16)  # Attempt to convert the string to an integer in base 16
            # Check if the length of the string is even (since a hex digest is two characters per byte)
            if len(data) % 2 == 0:
                return data
            else:
                raise ValueError("invalid hex")
        except:
            raise ValueError("invalid string")
            
            
    else:
        return "unknown type"
