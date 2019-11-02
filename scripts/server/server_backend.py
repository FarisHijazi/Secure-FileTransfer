import argparse
import os
import shlex
import socket
import subprocess
import json
import secrets

import os, sys, inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from utils import send_msg, recv_msg, SafeArgumentParser, AttrDict
from encryption_utils import CipherLib, _string_to_bytes, _bytes_to_string

os.chdir(os.path.dirname(os.path.realpath(__file__)))  # move path to file dir, to access files

# 256 bits = 32 bytes
# b'c37ddfe20d88021bc66a06706ac9fbdd0bb2dc0b043cf4d22dbbbcda086f0f48'
DEFAULT_KEY = _bytes_to_string(
    b'\xc3\x7d\xdf\xe2\x0d\x88\x02\x1b\xc6\x6a\x06\x70\x6a\xc9\xfb\xdd\x0b\xb2\xdc\x0b\x04\x3c\xf4\xd2\x2d\xbb\xbc\xda\x08\x6f\x0f\x48')


def getArgParser():
    parser = argparse.ArgumentParser("Server side app")
    parser.add_argument('--port', default=65432, type=int,
                        help='Port to listen on (non-privileged ports are > 1023)')
    parser.add_argument('--host', default='127.0.0.1', type=str,
                        help='the ipv4 address to open connections')
    return parser


def getClientArgParser():
    parser = SafeArgumentParser("\nServer side" +
                                "\nFaris Hijazi s201578750 25-09-19." +
                                "\n=======================================")

    # creating subcommands
    subparsers = parser.add_subparsers(help='commands help...')


    # https://docs.python.org/2/library/argparse.html#action-classes
    # class argparse.Action(option_strings, dest, nargs=None, const=None, default=None, type=None, choices=None, required=False, help=None, metavar=None)
    class ChooseCypherAction(argparse.Action):
        def __call__(self, parser, namespace, values, *args, **kwargs):
            """
            :param parser - The ArgumentParser object which contains this action.

            :param namespace - The Namespace object that will be returned by parse_args(). Most actions add an attribute to this object using setattr().

            :param values - The associated command-line arguments, with any type conversions applied. Type conversions are specified with the type keyword argument to add_argument().

            :param option_string - The option string that was used to invoke this action.
                The option_string argument is optional, and will be absent if the action is associated with a positional argument.

            :param args:
            :param kwargs:
            :return:
            """
            print('action args:')
            setattr(namespace, 'cipherfunc', getattr(CipherLib, values))

    ciphers = list(filter(lambda s: not str(s).startswith('__'), CipherLib.__dict__.keys()))

    parser.add_argument('-c', '--cipher', default='none', choices=ciphers, action=ChooseCypherAction,
                        help='The encryption/decryption algorithm to use when receiving the file.'
                             'Applies to both "put" and "pull". Default: none')
    parser.add_argument('-k', '--key', default=DEFAULT_KEY,  # 256 bits = 32 bytes
                        help='The key used for encryption/decryption.'
                             'Default: random')


    parser_quit = subparsers.add_parser('quit',
                                        help='quit the program')
    parser_quit.set_defaults(function=quit)

    parser_get = subparsers.add_parser('get',
                                       help='pull a file from the server')
    parser_get.add_argument('filename', type=str)
    parser_get.add_argument('-i', '--file-index', action='store_true')
    parser_get.set_defaults(function=get, type=str)

    parser_put = subparsers.add_parser('put',
                                       help='push a file to the server')
    parser_put.add_argument('-i', '--file-index', action='store_true')
    parser_put.add_argument('filename', type=str)
    parser_put.set_defaults(function=put, type=str)

    parser_ls = subparsers.add_parser('ls',
                                      help='list available files')
    # parser_ls.add_argument()
    parser_ls.set_defaults(function=ls)
    return parser


def recv_next_command(conn: socket, client_parser=None):
    """
    waits for a command by the client, and returns the parsed args,
    responds to the client with 202 and data on success

    :param conn: socket connection
    :return: client command arguments, or None if invalid command
    """
    command_json = _bytes_to_string(recv_msg(conn))
    print("received req:", command_json)

    try:
        #
        #
        #
        client_args = {  # extend defaults
            'file_index': None,
            'local': False,
            'key': DEFAULT_KEY,
            'cipher': 'none',
            'filename': '',
            'function': lambda x: None,
            'iv': None,
        }
        client_args.update(json.loads(command_json))  # update
        client_args = AttrDict(client_args)

        # converting args (parsing strings to bytes and function names to functions)
        client_args.cipherfunc = getattr(CipherLib, client_args.cipher)
        client_args.iv = _string_to_bytes(client_args.iv)
        client_args.function = eval(client_args.function)

        # printing object:
        import pprint
        pp = pprint.PrettyPrinter(indent=4)
        print('client_args received')
        pp.pprint(vars(client_args))

        #

        server_resp = _string_to_bytes(json.dumps({
            'readystate': 202,  # code "202" meaning (accepted)
        }))
        send_msg(conn, server_resp)
        return client_args
    except Exception as e:
        print("ERROR executing command:", e)
        return None


# ======== server actions =====
# these actions/commands are with respect to the client,
# so get() means the server will send to the client, while put() receives a file from the client

def get(conn: socket, args=None):
    # send the file to client
    if args.file_index:
        args.filename = os.listdir('files')[int(args.filename)]

    iv = secrets.token_bytes(16)
    args_filename = args.filename
    filename = os.path.join('files', args_filename)
    with open(filename, 'rb') as f:
        plaintext = f.read()
        ciphertext = args.cipherfunc(data=plaintext, key=args.key, iv=iv)
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
    client_data = AttrDict(json.loads(_bytes_to_string(recv_msg(conn))))

    args.filename = os.path.join('files', args.filename)

    data = client_data.data

    if data is None:
        print("Problem: data received is None")
    print("got the file data!: {}Bytes".format(len(data)))

    if not os.path.isdir('./files'):
        os.mkdir('./files')

    with open(args.filename, 'wb+') as file:
        plaintext = args.cipherfunc(data=data, key=args.key, decrypt=True, iv=client_data.iv)
        file.write(plaintext)

    print('recieved file:', args.filename)

    if os.path.isfile(args.filename):
        subprocess.Popen(r'explorer /select,"{}"'.format(args.filename))


def ls(conn: socket, args=None):
    # send list of files
    filelist = os.listdir('files/')
    filelist_json = json.dumps(filelist)
    send_msg(conn, _string_to_bytes(filelist_json))
