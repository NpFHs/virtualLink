import rsa

public_key, private_key = rsa.newkeys(512)


def encrypt(message):
    enc = rsa.encrypt(message.encode(), public_key)

    new_enc = enc.replace(b"\n", b"").replace(b"\r", b"")
    return enc
