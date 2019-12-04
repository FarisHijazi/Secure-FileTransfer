# @author Faris Hijazi


import inspect
import os
import sys

DESCRIPTION = ("COE451 ProgAssignment1: SFTP client-server."
               "\nClient side" +
               "\nFaris Hijazi s201578750 25-09-19." +
               "\n=======================================")

# moving the import path 1 directory up (to import utils)
from client_backend import get_arg_parser, get_user_commands, exec_function
from authentication import authenticate


# HOST = '127.0.0.1'  # The server's hostname or IP address
# PORT = 65432        # The port used by the server


def main():
    parser = get_arg_parser()
    print(DESCRIPTION + "\n")

    args = None

    i = 0
    while True:
        i += 1
        args = get_user_commands(parser, args)

        if vars(args)['auth']:
            print('Client: authenticating server...')
            authenticate(args)

        resp = exec_function(args)


if __name__ == "__main__":
    main()
