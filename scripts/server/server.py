import os
import socket

# moving the import path 1 directory up (to import utils)

os.chdir(os.path.dirname(os.path.realpath(__file__)))  # move path to file dir, to access files

from server_backend import getArgParser, recv_next_command
from utils import recv_msg

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)

# this parser is to parse the client commands (not the commandline parser)


if __name__ == "__main__":
    print("COE451 ProgAssignment1: SFTP client-server."
          "\nServer side" +
          "\nFaris Hijazi s201578750 25-09-19." +
          "\n=======================================")
    parser = getArgParser()
    args = parser.parse_args()

    i = 0
    while True:
        i += 1
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((args.host, args.port))
            s.listen(10)
            print("waiting for clients to connect...")
            conn, addr = s.accept()
            with conn:
                print('Connected by', addr)
                client_args = recv_next_command(conn)
                try:
                    result = client_args.function(conn, client_args)

                    final_client_resp = recv_msg(conn)
                    if final_client_resp in [r'200']:
                        print("Transaction completed successfully")
                except Exception as e:
                    print("Error:", e)
                    continue

                # then based on the request, do the action
                # the request is basically an argument string, can be parsed by the argparser

        print("Closing connection")
