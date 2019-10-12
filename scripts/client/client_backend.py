import argparse
import os
import shlex
import socket
import subprocess
import sys

from utils import recv_msg, send_msg
from encryption_utils import CipherLib


def sendCommand(args, callback=lambda sock: print("connected", sock)):
    """
    @param args -   this object is similar to the one parsed from the commandline, contains "host" and "port" members
    @param callback(sock) - a function to call on success (gets passed the socket object, the socket object at this point is already connected and is ready to send or recv)
    @returns the callback result
    """

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print('connecting to server...', end='')
        s.connect((args.host, args.port))  # connect
        print('\rConnection established                       ')
        # if args._line_args:
        send_msg(s, args._line_args.encode('utf-8'))  # send the command line
        print('Sending command: "{}"'.format(args._line_args))
        # check if server acknowledged the command
        # (if resp is included in one of the success response codes)
        resp = recv_msg(s)
        if resp in [b'202']:
            res = callback(s)
            send_msg(s, b'200')  # send OK code
            print('\nTransaction complete')
            return res


def get_user_commands(parser: argparse.ArgumentParser, args=None):
    # the returned agrs object will also have a member args._line_args
    # parsing args
    line_args = ''

    if not args:
        args = parser.parse_args()
        if hasattr(args, 'function'):  # arguments passed (if first time)
            line_args = ' '.join(sys.argv[1:])
            sys.argv = [sys.argv[0]]  # clear CLI args

    if not line_args:  # no args passed
        done = False
        while not done:
            parser.print_usage()
            values_as_strings = [(v.__name__ if hasattr(v, '__name__') else str(v)) for v in args.__dict__.values()]
            args_str = dict(zip(args.__dict__.keys(), values_as_strings))

            print("Current arg values:", args_str)
            line_args = input('Client\n$ ')
            print()

            try:
                args = parser.parse_args(shlex.split(line_args))
                done = True  # keep trying and break when successful
            except Exception as e:
                print(e)

    setattr(args, '_line_args', line_args)
    return args


def exec_function(args):
    if not hasattr(args, 'function'):
        return

    return args.function(args)


def getArgParser():
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
            setattr(namespace, 'cipher', CipherLib.__dict__.get(values, CipherLib.none))

    ciphers = list(filter(lambda s: not str(s).startswith('__'), CipherLib.__dict__.keys()))

    parser.add_argument('-c', '--cipher', default=None, choices=ciphers, action=ChooseCypherAction,
                        help='The encryption/decryption algorithm to use when receiving the file.'
                             'Applies to both "put" and "pull". Default: none')
    parser.add_argument('-k', '--key', default=b'c37ddfe20d88021bc66a06706ac9fbdd0bb2dc0b043cf4d22dbbbcda086f0f48',  # 256 bits = 32 bytes
                        help='The key used for encryption/decryption.'
                             'Default: random')

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


def get(args=[]):
    if args.file_index:
        args.filename = 'file.gif'

    if not os.path.isdir('./files'):
        os.mkdir('./files')

    filename = args.filename
    if not filename.startswith('files'):
        filename = os.path.join('files', args.filename)

    if os.path.isdir(filename):
        args.filename = os.path.join(args.filename, 'file.gif')


    def callback(conn: socket):
        data = recv_msg(conn)

        with open(filename, 'wb+') as f:
            plaintext = args.cipher(data=data, key=args.key, decrypt=True)
            f.write(plaintext)
            if os.path.isfile(filename):
                subprocess.Popen(r'explorer /select,"{}"'.format(filename))

    return sendCommand(args, callback)


def put(args=[]):
    if args.file_index:  # if access-by-fileindex, then remove attr (to prevent issues) and get filename
        delattr(args, 'file_index')
        file_index = int(args.filename)
        args.filename = ls_local(args)[file_index]

    filename = os.path.join('files', args.filename)  # prepend 'file/'

    if not os.path.isfile(filename):  # check if file exists
        print("File {} doesn't exist".format(filename))
        return

    ciphertext = b''
    with open(filename, 'rb') as f:
        data = f.read()
        ciphertext = args.cipher(data=data, key=args.key)

    callback = lambda conn: send_msg(conn, ciphertext)

    return sendCommand(args, callback)


def ls(args=[]):
    """
    list files, either local or online (depending on --local argument)
    """
    if args.local:
        return ls_local(args, True)
    else:
        return ls_remote(args)


def ls_local(args=[], print_list=False):
    filelist = os.listdir('files/')
    if print_list:
        prettystr = '\n'.join(['\t{} | \t{}'.format(i, file)
                               for i, file in enumerate(filelist)])
        print("List of server files:\n", prettystr)
    return filelist


def ls_remote(args=[]):
    def callback(conn: socket):
        import json
        res = recv_msg(conn)

        filelist = json.loads(res)
        prettystr = '\n'.join(['\t{} | \t{}'.format(i, file)
                               for i, file in enumerate(filelist)])
        print("List of server files:\n", prettystr)
        return filelist

    return sendCommand(args, callback)


def quit(args=[]):
    exit(0)
