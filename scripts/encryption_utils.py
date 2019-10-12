import pyaes
import os


class CipherLib:
    """
    contains all the encryption libs

    format of each
    """

    def __init__(self):
        raise Exception("Cannot instantiate type " + self.__class__)

    def none(data, decrypt=False, key=None, **kwargs) -> bytes:
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        return data

    def aes(data, decrypt=False, key: str = None, **kwargs) -> bytes:
        # A 256 bit (32 byte) key

        if key is None:
            print("empty AES key:", key)
            return data

        # key must be bytes, so we convert it
        if isinstance(key, str):
            key = key.encode('utf-8')

        aes = pyaes.AESModeOfOperationCTR(key)

        data = aes.decrypt(data) if decrypt \
            else aes.encrypt(data)

        print("encryption/decryption data:", data)
        return data
