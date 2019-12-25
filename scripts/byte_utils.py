import array
import types
from copy import deepcopy
import json

def make_args_map(args: dict) -> dict:
    """
    prepares this args dict for being JSON serialized

    adds a '__map' attribute which maps each member to its type,
    so that we can do backward translation
    """

    if type(args) is not dict:
        raise Exception('args must be of type dict')

    if '__map' in args:
        raise Exception('make_args_map(): "args" already has a "__map":', args)

    args = deepcopy(args)

    __map = {}
    for k, v in args.items():
        if isinstance(v, types.FunctionType):  # functions get the name passed
            args[k] = v.__name__
            __map[k] = 'function'
        elif isinstance(v, bytes):  # bytes get turned into strings
            args[k] = _bytes_to_string(v)
            __map[k] = 'bytes'
        elif isinstance(v, dict):
            print('make_args_map(): dict type encountered:', v)
            make_args_map(args[k])
    
    args['__map'] = __map
    return args

def apply_args_map(args: dict) -> dict:
    if type(args) is not dict:
        raise Exception('args must be of type dict')
    if '__map' not in args:
        raise Exception('apply_args_map(): "args" does not have "__map":', args)
    
    args = deepcopy(args)
    
    for k, arg_type in args['__map'].items():
        if arg_type == 'function':
            args[k] = eval(args[k])
        elif arg_type == 'bytes':
            args[k] = _string_to_bytes(args[k])
        elif arg_type == 'dict':
            print('apply_args_map(): dict type encountered:', arg_type)
            apply_args_map(args[k])
    
    del args['__map']
    return args


def _string_to_bytes(text):
    if text is None:
        text = ''
    array_array = array.array('B', list(ord(c) for c in text))
    return bytes(array_array)

def _bytes_to_string(binary):
    if binary is None:
        binary = b''
    return "".join(chr(b) for b in binary)


def ensure_bytes(x):
    # ensures that the data type is bytes (if string or None were passed)
    if isinstance(x, (array.array)):
        x = bytes(x)
    if isinstance(x, (str)):
        x = _string_to_bytes(x)
    return x


def RepresentsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def int_to_bytes(x: int) -> bytes:
    return x.to_bytes((x.bit_length() + 7) // 8, 'big')


def int_from_bytes(xbytes: bytes) -> int:
    return int.from_bytes(xbytes, 'big')



def args2msg(args:dict) -> bytes:
    return _string_to_bytes(json.dumps(make_args_map(args)))

def msg2args(args:bytes) -> dict:
    return apply_args_map(json.loads(_bytes_to_string(args)))
