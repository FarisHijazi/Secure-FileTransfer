import argparse
import os
import shlex
import socket
import subprocess

from server import client_parser
from utils import send_msg, recv_msg, SafeArgumentParser


def getArgParser():
    parser = argparse.ArgumentParser("Server side app")
    parser.add_argument('--port', default=65432, type=int,
                        help='Port to listen on (non-privileged ports are > 1023)')
    parser.add_argument('--host', default='127.0.0.1',
                        type=str, help='the ipv4 address to open connections')
    return parser


def getClientArgParser():
    parser = SafeArgumentParser("\nServer side" +
                                "\nFaris Hijazi s201578750 25-09-19." +
                                "\n=======================================")

    # creating subcommands
    subparsers = parser.add_subparsers(help='commands help...')
    parser_quit = subparsers.add_parser('quit', help='quit the program')
    parser_quit.set_defaults(function=quit)

    parser_get = subparsers.add_parser(
        'get', help='pull a file from the server')
    parser_get.add_argument('filename', type=str)
    parser_get.add_argument('-i', '--file-index', action='store_true')
    parser_get.set_defaults(function=get, type=str)

    parser_put = subparsers.add_parser('put', help='push a file to the server')
    parser_put.add_argument('filename', type=str)
    parser_put.set_defaults(function=put, type=str)

    parser_ls = subparsers.add_parser('ls', help='list available files')
    # parser_ls.add_argument()
    parser_ls.set_defaults(function=ls)
    return parser


def recv_next_command(conn: socket):
    """
    waits for a command by the client, and returns the parsed args, responds to the client with 202 on success
    :param conn: socket connection
    :return: client command arguments, or None if invalid command
    """
    req = recv_msg(conn)
    command = req.decode('utf-8')
    print("received req:", command)

    try:
        client_args = client_parser.parse_args(shlex.split(command))
        send_msg(conn, b'202')  # send the code "202" meaning (accepted)
        return client_args
    except Exception as e:
        print(e)
        return None


# ======== server actions =====
# these actions/commands are with respect to the client,
# so get() means the server will send to the client, while put() receives a file from the client

def get(conn: socket, args=[]):
    # send the file to client
    if args.file_index:
        args.filename = os.listdir('files')[int(args.filename)]

    args_filename = args.filename
    filename = os.path.join('files', args_filename)
    with open(filename, 'rb') as f:
        data = f.read()
    print("finished reading file \"{}\", {}B".format(filename, len(data)))
    send_msg(conn, data)


def put(conn: socket, args=[]):
    print('receiving file...')
    args.filename = os.path.join('files', args.filename)
    # recv file from client
    data = recv_msg(conn)
    print("got the file data!: {}Bytes".format(len(data)))

    if not os.path.isdir('./files'):
        os.mkdir('./files')

    with open(args.filename, 'wb+') as file:
        file.write(data)

    print('recieved file:', args.filename)

    if os.path.isfile(args.filename):
        subprocess.Popen(r'explorer /select,"{}"'.format(args.filename))


def ls(conn: socket, args=[]):
    import json
    # send list of files
    filelist = os.listdir('files/')
    filelist_json = json.dumps(filelist)
    send_msg(conn, filelist_json.encode('utf-8'))
