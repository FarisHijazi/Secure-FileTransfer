import array


def main():
    # code here
    return


if __name__ == '__main__':
    main()


def _string_to_bytes(text):
    if text is None:
        text = ''
    array_array = array.array('B', list(ord(c) for c in text))
    return bytes(array_array)


def _bytes_to_string(binary):
    if binary is None:
        binary = b''
    return "".join(chr(b) for b in binary)


def ensure_bytes(x):
    # ensures that the data type is bytes (if string or None were passed)
    if isinstance(x, (array.array)):
        x = bytes(x)
    if isinstance(x, (str)):
        x = _string_to_bytes(x)
    return x


def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def int_to_bytes(x: int) -> bytes:
    return x.to_bytes((x.bit_length() + 7) // 8, 'big')


def int_from_bytes(xbytes: bytes) -> int:
    return int.from_bytes(xbytes, 'big')