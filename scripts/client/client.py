# @author Faris Hijazi


import inspect
import os
import sys

DESCRIPTION = ("COE451 ProgAssignment1: SFTP client-server."
               "\nClient side" +
               "\nFaris Hijazi s201578750 25-09-19." +
               "\n=======================================")

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

os.chdir(os.path.dirname(os.path.realpath(__file__)))

# moving the import path 1 directory up (to import utils)
from client_backend import get_arg_parser, get_user_commands, exec_function


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
        resp = exec_function(args)


if __name__ == "__main__":
    main()
