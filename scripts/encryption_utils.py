import pyaes
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
        if isinstance(data, bytes):
            data = data.decode('utf-8')
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

        # key must be bytes, so we convert it
        if isinstance(key, str):
            key = key.encode('utf-8')

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

        # performing the operation (encryption or decryption)
        new_data = b''.join((map(operation, chunks)))

        print(('descrypted' if decrypt else 'encrypted') + ' data', new_data)

        return new_data
