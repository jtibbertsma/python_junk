from hashlib import sha256

def crack(hash):
    for n in range(10000):
        if sha256(bytes(f'{n:04d}', 'ascii'), usedforsecurity=False).hexdigest() == hash:
            return n

print(crack('f478525457dcd5ec6223e52bd3df32d1edb600275e18d6435cdeb3ef2294e8de'))
