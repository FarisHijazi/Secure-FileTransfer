import pyaes

from byte_utils import _string_to_bytes, ensure_bytes


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

        # converting values to bytes
        key = ensure_bytes(key)
        data = ensure_bytes(data)
        iv_128= ensure_bytes(iv_128)


        aes = pyaes.AESModeOfOperationCBC(key, iv=iv_128)

        operation = aes.decrypt if decrypt else aes.encrypt

        chunks = pad_and_partition(data, block_size=16)
        # performing the operation (encryption or decryption)
        new_data = b''.join((map(operation, chunks)))

        # print(('descrypted' if decrypt else 'encrypted') + ' data', new_data)

        return new_data


### ======== helper functions ==========


def pad_and_partition(data, block_size=16):
    # padding (to be a multiple of 16)
    remainder = len(data) % block_size
    padding = bytes((block_size - remainder) % block_size)
    padded_data = b"".join([data, padding])
    # split to blocks and encrypt/decrypt each one
    n_blocks = len(padded_data) // block_size
    chunks = [padded_data[i * block_size:(i + 1) * block_size] for i in range(n_blocks)]
    return chunks


