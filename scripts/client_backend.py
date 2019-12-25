import argparse
import json
import os
import secrets
import shlex
import socket
import subprocess
import sys
import types
from copy import deepcopy

from utils import recv_msg, send_msg, AttrDict, path_leaf
from encryption_utils import CipherLib
from byte_utils import _string_to_bytes, _bytes_to_string

# 256 bits = 32 bytes
# b'c37ddfe20d88021bc66a06706ac9fbdd0bb2dc0b043cf4d22dbbbcda086f0f48'
DEFAULT_KEY = _bytes_to_string(
    b'\xc3\x7d\xdf\xe2\x0d\x88\x02\x1b\xc6\x6a\x06\x70\x6a\xc9\xfb\xdd\x0b\xb2\xdc\x0b\x04\x3c\xf4\xd2\x2d\xbb\xbc\xda\x08\x6f\x0f\x48')


def send_command(args, callback=lambda sock: print("Connected", sock)):
    """connects to the server and sends the command

    :param args:   this object is similar to the one parsed from the commandline,
        contains "host" and "port" members
    :param callback(sock, respjson): a function to call when connected to the server.
        sock:   Gets passed the socket object, the socket object at this point is already connected and is ready to send or recv.
    :return the callback result
    """

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print('connecting to server...', end='')
        s.connect((args['host'], args['port']))  # connect
        print('\rConnection established                       ')

        args['auth'] = False
        # setup IV
        args['iv'] = secrets.token_bytes(16)
        request_json = format_args_to_json(args)

        # send the command/request json
        send_msg(s, _string_to_bytes(request_json))

        # check if server acknowledged the command
        # (if resp is included in one of the success response codes)
        resp = recv_msg(s)
        resp_json = json.loads(_bytes_to_string(resp))
        if resp_json['readystate'] in [202]:
            res = callback(s)

            send_msg(s, b'200')  # send OK code
            print('\nTransaction complete')
            return res


def format_args_to_json(args: dict) -> str:
    """
    prepare these args to be sent to the server as json string
    :param args: args dict
    :returns a copied formatted dict json string
    """

    if 'cipherfunc' not in args:
        args['cipherfunc'] = CipherLib.none

    #

    import copy
    s_args = copy.deepcopy(args)
    for k, v in s_args.items():
        if isinstance(v, types.FunctionType):  # functions get the name passed
            s_args[k] = v.__name__
        elif isinstance(v, bytes):  # bytes get turned into strings
            s_args[k] = _bytes_to_string(v)

    s_args['cipher'] = s_args.get('cipherfunc', 'none')
    del s_args['key']  # delete key (otherwise is sent in plaintext)
    if 'sesskey' in s_args:
        del s_args['sesskey']

    request_json = json.dumps(s_args)

    # print('Sending command: "{}"'.format(request_json))
    return request_json


def get_user_commands(parser: argparse.ArgumentParser, args=None):
    # the returned args object will also have a member args._line_args
    # parsing args
    line_args = ''

    if not args:
        args = vars(parser.parse_args())
        if 'function' in args:  # arguments passed (if first time)
            line_args = ' '.join(sys.argv[1:])
            sys.argv = [sys.argv[0]]  # clear CLI args

    if not line_args:  # no args passed
        done = False
        while not done:
            parser.print_usage()

            line_args = input('Client\n$ ')
            print()

            try:
                args = vars(parser.parse_args(shlex.split(line_args)))
                done = True  # keep trying and break when successful
            except Exception as e:
                print("ERROR:", e)

    args['_line_args'] = line_args
    return args


def exec_function(args: dict):
    if 'function' in args:
        return args['function'](args)


def get_arg_parser():
    """
    creating the command parser object
    """
    parser = argparse.ArgumentParser(description="Connect to server")

    # act normally in the beginning (from the command line)
    parser.add_argument('--port', default=65432, type=int,
                        help='port to listen on (non-privileged ports are > 1023).'
                             'Default: 65432')
    parser.add_argument('--host', default='127.0.0.1', type=str,
                        help='hostname or ipv4 address to connect to (use ip address for consistency).'
                             'Default: "127.0.0.1"')

    parser.add_argument('--auth', default=True, action='store_true',
                        help='Perform authentication and establish a session key')

    parser.add_argument('--test', default=0, type=int,
                        help='These are the test cases for the authentication, by default, test cases are off')

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
                        help='The key used for encryption/decryption.')

    # creating subcommands
    subparsers = parser.add_subparsers(help='commands help...')

    # help
    parser_help = subparsers.add_parser('help', help='Display help message and usage')
    parser_help.set_defaults(function=lambda args: parser.print_help())

    # quit
    parser_quit = subparsers.add_parser('quit', help='quit the program', aliases=['q', 'exit'])
    parser_quit.set_defaults(function=quit)

    # get
    parser_get = subparsers.add_parser('get', help='pull a file from the server', aliases=[])
    parser_get.add_argument('filename', type=str)
    parser_get.add_argument('-i', '--file-index', action='store_true',
                            help='Enable file-access by index, rather than by specifying the path.'
                                 '\nUse "ls" to see the corresponding index to each file')
    parser_get.set_defaults(function=get)

    # put
    parser_put = subparsers.add_parser('put', help='push a file to the server (or locally)', aliases=[])
    parser_put.add_argument('-i', '--file-index', action='store_true',
                            help='Enable file-access by index, rather than by specifying the path.'
                                 '\nUse "ls -l" to list local files and see the corresponding index to each file')
    parser_put.add_argument('filename',
                            # widget='FileChooser'
                            )
    parser_put.set_defaults(function=put)

    # ls
    parser_ls = subparsers.add_parser('ls', help='list available files on the server', aliases=[])
    parser_ls.add_argument('-l', '--local', action='store_true', help='List files found locally (client side)')
    parser_ls.set_defaults(function=ls)
    return parser


# ============ client actions =======


def get(args: dict):
    def callback(conn: socket):
        # receive data
        resp = json.loads(_bytes_to_string(recv_msg(conn)))

        if 'file_index' in args and args['file_index'] == True:
            args['filename'] = resp['filename']
            del args['file_index']

        if not os.path.isdir('./client_files'):
            os.mkdir('./client_files')

        filename = os.path.join('client_files', path_leaf(args['filename']))

        if os.path.isdir(filename):
            args['filename'] = os.path.join(args['filename'], resp['filename'])

        # === done preparing filesystem ===

        with open(filename, 'wb+') as f:
            plaintext = args['cipherfunc'](data=resp['data'], key=args['key'], decrypt=True, iv=resp['iv'])
            f.write(plaintext)
            if os.path.isfile(filename):
                subprocess.Popen(r'explorer /select,"{}"'.format(filename))

    return send_command(args, callback)


def put(args: dict):
    
    args['iv'] = secrets.token_bytes(16)

    if 'file_index' in args and args['file_index'] == True:  # if access-by-fileindex, then remove attr (to prevent issues) and get filename
        del args['file_index']
        file_index = int(args['filename'])
        args['filename'] = ls_local(args)[file_index]

    filename = os.path.join('client_files', path_leaf(args['filename']))

    if not os.path.isfile(filename):  # check if file exists
        print('ERROR: File "{}" doesn\'t exist'.format(filename))
        return

    def callback(conn: socket):
        ciphertext = b''
        with open(filename, 'rb') as f:
            data = f.read()
            ciphertext = args['cipherfunc'](data=data, key=args['key'], iv=args['iv'])

        return send_msg(
            conn,
            _string_to_bytes(json.dumps({
                'filename': filename,
                'data': _bytes_to_string(ciphertext),
                'iv': _bytes_to_string(args['iv']),
            }))
        )

    return send_command(args, callback)


def ls(args: dict):
    """
    list client_files, either local or online (depending on --local argument)
    """
    if args['local'] == True:
        return ls_local(args, True)
    else:
        return ls_remote(args)


def ls_local(args: dict, print_list=False):
    filelist = os.listdir('client_files/')
    if print_list:
        prettystr = '\n'.join(['\t{} | \t{}'.format(i, file)
                               for i, file in enumerate(filelist)])
        print("List of server client_files:\n", prettystr)
    return filelist


def ls_remote(args: dict):
    def callback(conn: socket):
        filelist = json.loads(recv_msg(conn))
        prettystr = '\n'.join(['\t{} | \t{}'.format(i, file)
                               for i, file in enumerate(filelist)])
        print("List of server client_files:\n", prettystr)
        return filelist

    return send_command(args, callback)


def quit(args=None):
    exit(0)
