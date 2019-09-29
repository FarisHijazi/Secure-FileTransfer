import argparse
import inspect
import os
import shlex
import socket
import subprocess
import sys


# moving the import path 1 directory up (to import utils)
currentdir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from utils import recv_msg, send_msg  # this must be after changing the directory

DESCRIPTION = ("COE451 ProgAssignment1: SFTP client-server."
               "\nClient side" +
               "\nFaris Hijazi s201578750 25-09-19." +
               "\n=======================================")

# https://realpython.com/python-sockets/#background
os.chdir(os.path.dirname(os.path.realpath(__file__)))


# HOST = '127.0.0.1'  # The server's hostname or IP address
# PORT = 65432        # The port used by the server


def get(args=[]):
    def callback(conn: socket):
        data = recv_msg(conn)

        if args.file_index:
            args.filename = 'file.gif'

        if not os.path.isdir('./files'):
            os.mkdir('./files')

        if not args.filename.startswith('files'):
            filename = os.path.join('files', args.filename)

        if os.path.isdir(args.filename):
            args.filename = os.path.join(args.filename, 'file.gif')

        with open(filename, 'wb+') as f:
            f.write(data)
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

    def callback(conn: socket):
        with open(filename, 'rb') as f:
            data = f.read()
            send_msg(conn, data)

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


# ====== end of defining actions ======

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


def get_user_commands(parser: argparse.ArgumentParser):
    # the returned agrs object will also have a member args._line_args
    # parsing args
    args = parser.parse_args()
    line_args = ''
    if hasattr(args, 'function'):  # arguments passed (if first time)
        setattr(args, '_line_args', ' '.join(sys.argv[1:]))
        sys.argv = [sys.argv[0]]  # clear CLI args
    else:  # no args passed
        done = False
        while not done:
            parser.print_usage()
            line_args = input('Client\n$ ')
            print()

            try:
                args = parser.parse_args(shlex.split(line_args))
                # if hasattr(args, 'filename'):
                #     args.filename = args.filename
                done = True  # keep trying and break when successful
            except Exception as e:
                print(e)

    setattr(args, '_line_args', line_args)
    return args


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


def exec_function(args):
    if not hasattr(args, 'function'):
        return

    try:
        return args.function(args)
    except Exception as e:
        print("Error executing command:", e)


def main():
    parser = getArgParser()
    print(DESCRIPTION + "\n")

    i = 0
    while True:
        i += 1
        args = get_user_commands(parser)
        resp = exec_function(args)


if __name__ == "__main__":
    main()
