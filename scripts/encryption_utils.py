import pyaes
import array, struct

import os


class CipherLib:
    """
    contains all the encryption libs

    format of each
    """

    def __init__(self):
        raise Exception("Cannot instantiate type " + self.__class__.__name__)

    @staticmethod
    def none(data, decrypt=False, key=None, **kwargs) -> bytes:
        if isinstance(data, str):
            data = _string_to_bytes(data)
        return data

    @staticmethod
    def aes(data, decrypt=False, key=None, **kwargs) -> bytes:
        """
        :param data: data as string or bytes
        :param decrypt: decrypt or encrypt?
        :param key: A 256 bit (32 byte) key
        :param kwargs:
        :return:

        ```
        aes(data, decrypt=False, iv='intializationVec')
        ```
        """

        if key is None:
            print("empty AES key:", key)
            return data

        iv_128 = kwargs.get('iv', None)
        aes = pyaes.AESModeOfOperationCBC(key, iv=iv_128)

        operation = aes.decrypt if decrypt else aes.encrypt

        block_size = 16
        # padding (to be a multiple of 16)
        remainder = len(data) % block_size
        padded_data = b"".join([data, bytes(block_size - remainder)])

        # split to blocks and encrypt/decrypt each one
        n_blocks = len(padded_data) // block_size
        chunks = [padded_data[i * block_size:(i + 1) * block_size] for i in range(n_blocks)]

def _string_to_bytes(text):
    if text is None:
        text = ''
    array_array = array.array('B', list(ord(c) for c in text))
    print(array_array)
    return bytes(array_array)


def _bytes_to_string(binary):
    if binary is None:
        binary = b''
    return "".join(chr(b) for b in binary)
