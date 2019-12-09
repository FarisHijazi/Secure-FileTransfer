import argparse
import struct


class ArgumentParserError(Exception):
    pass


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # this is what decides if the parser should be safe or not
        if hasattr(self, 'errorlevel') and getattr(self, 'errorlevel'):
            super().error(message)
        else:
            print("Argument parse error:", message)
            pass


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


# the bellow was taken from the answer here:
# https://stackoverflow.com/a/17668009/7771202

def send_msg(sock, msg):
    # Prefix each message with a 4-byte length (network byte order)
    msg = struct.pack('>I', len(msg)) + msg
    sock.sendall(msg)


def recv_msg(sock):
    # Read message length and unpack it into an integer
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return recvall(sock, msglen)


def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data
