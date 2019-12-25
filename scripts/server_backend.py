import argparse
import socket
import subprocess
import json
import secrets

import os, sys, inspect

from utils import send_msg, recv_msg, SafeArgumentParser, AttrDict, path_leaf
from encryption_utils import CipherLib
from byte_utils import _string_to_bytes, _bytes_to_string

# 256 bits = 32 bytes
# b'c37ddfe20d88021bc66a06706ac9fbdd0bb2dc0b043cf4d22dbbbcda086f0f48'
DEFAULT_KEY = _bytes_to_string(
    b'\xc3\x7d\xdf\xe2\x0d\x88\x02\x1b\xc6\x6a\x06\x70\x6a\xc9\xfb\xdd\x0b\xb2\xdc\x0b\x04\x3c\xf4\xd2\x2d\xbb\xbc\xda\x08\x6f\x0f\x48')


def get_arg_parser():
    parser = argparse.ArgumentParser("Server side app")
    parser.add_argument('--port', default=65432, type=int,
                        help='Port to listen on (non-privileged ports are > 1023)')
    parser.add_argument('--host', default='127.0.0.1', type=str,
                        help='the ipv4 address to open connections')
    return parser


def parse_command_json(command_json):
    client_args = {  # extend defaults
        'auth': True,
        'file_index': None,
        'local': False,
        'key': DEFAULT_KEY,
        'cipher': 'none',
        'filename': '',
        'function': lambda x: None,
        'iv': None,
    }
    client_args.update(json.loads(command_json))  # update
    # converting args (parsing strings to bytes and function names to functions)
    client_args['cipherfunc'] = getattr(CipherLib, client_args['cipher'])
    client_args['iv'] = _string_to_bytes(client_args['iv'])
    client_args['function'] = eval(client_args['function'])

    # printing object:
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    print('client_args received')
    pp.pprint(client_args)

    return client_args


def recv_next_command(conn: socket, client_parser=None):
    """
    waits for a command by the client, and returns the parsed args,
    responds to the client with 202 and data on success

    :param conn: socket connection
    :return: client command arguments, or None if invalid command
    """
    command_json = _bytes_to_string(recv_msg(conn))
    print("received req:", command_json)

    client_args = parse_command_json(command_json)

    server_resp = _string_to_bytes(json.dumps({
        'readystate': 202,  # code "202" meaning (accepted)
    }))
    send_msg(conn, server_resp)
    return client_args

# ======== server actions =====
# these actions/commands are with respect to the client,
# so get() means the server will send to the client, while put() receives a file from the client

def get(conn: socket, args=None):
    # send the file to client
    if args['file_index']:
        args['filename'] = os.listdir('server_files')[int(args['filename'])]

    iv = secrets.token_bytes(16)
    print('iv=',iv)
    
    filename = os.path.join('server_files', path_leaf(args['filename']))
    with open(filename, 'rb') as f:
        plaintext = f.read()
        ciphertext = args['cipherfunc'](data=plaintext, key=args['key'], iv=iv)
    
    print("finished reading file \"{}\", {}B".format(filename, len(ciphertext)))

    return send_msg(
        conn,
        _string_to_bytes(json.dumps({
            'filename': filename,
            'data': _bytes_to_string(ciphertext),
            'iv': _bytes_to_string(iv),
        }))
    )


def put(conn: socket, args=None):
    # recv file from client and write to file
    print('receiving file...')
    client_data = json.loads(_bytes_to_string(recv_msg(conn)))

    args['filename'] = os.path.join('server_files', args['filename'])

    data = client_data['data']
    if data is None:
        print("Problem: data received is None")
    print("got the file data!: {}Bytes".format(len(data)))

    if not os.path.isdir('./server_files'):
        os.mkdir('./server_files')
    
    filename = os.path.join('server_files', path_leaf(args['filename']))
    
    print('iv=',client_data['iv'])

    with open(filename, 'wb+') as f:
        plaintext = args['cipherfunc'](data=data, key=args['key'], decrypt=True, iv=client_data['iv'])
        f.write(plaintext)

    print('recieved file:', args['filename'])

    if os.path.isfile(filename):
        subprocess.Popen(r'explorer /select,"{}"'.format(args['filename']))


def ls(conn: socket, args=None):
    # send list of files
    filelist = os.listdir('server_files/')
    filelist_json = json.dumps(filelist)
    send_msg(conn, _string_to_bytes(filelist_json))
