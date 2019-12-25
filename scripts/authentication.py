import json
import socket
import base64
import re

import sys, time, math
import secrets, hashlib, rsa
from copy import deepcopy
from cryptography.fernet import Fernet

from client_backend import format_args_to_json
from byte_utils import _string_to_bytes, _bytes_to_string, int_to_bytes, int_from_bytes, args2msg, msg2args, apply_args_map, make_args_map
from utils import send_msg, recv_msg, modinv, find_coprime
from encryption_utils import CipherLib


def authenticate(args, is_client=True, conn=None):
    ## setting up asymmetric key
    # n, e, d, q, p = init_asym_key(is_client)
    # pubkey = rsa.PublicKey(n, e)
    # privkey = rsa.PrivateKey(n, e, d, q, p)

    pubkey, privkey = rsa.newkeys(2048, poolsize=8)

    ## setting up Diffie Hellmen
    # Alice is the client, Bob is the server
    exp, g, m = init_DiffieHellman()
    # g_x_mod_m = (g ** exp) % m
    g_x_mod_m = exp_mod(g, exp, m)

    if is_client:
        name = "Alice"
    else:
        name = "Bob"

    ## Generating challenge
    r_challenge = int_from_bytes(secrets.token_bytes(256 // 8))  # 256-b = 8-B


    ## setting args attrs
    init_info = {
        'r_challenge': r_challenge,
        'name': name,
        'g_x_mod_m': g_x_mod_m,  # Diffie Hellman segment
        'n': pubkey.n,
        'e': pubkey.e,
    }

    name = _string_to_bytes(name)

    if is_client:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
            print('connecting to server...', end='')
            conn.connect((args['host'], args['port']))  # connect
            print('\rConnection established                       ')

            if 'test' in args and args['test']==2:
                privkey.d -= 1

            ##############
            # send msg 1 #
            ##############
            args['seq'] = 1
            args['msg1'] = init_info
            print('auth: sending auth command and msg1...:', list(args.keys()))
            send_msg(conn, _string_to_bytes(format_args_to_json(args)))

            # OK 200 response
            resp = json.loads(_bytes_to_string(recv_msg(conn)))
            if resp['readystate'] in [200]:
                print("ERROR: server did not respond with OK 200, terminating session...")
                return

            ##############
            # recv msg 2 #
            ##############
            msg2 = msg2args(recv_msg(conn))
            assert msg2['seq'] == 2
            print('auth: received msg 2:', list(msg2.keys()))

            info_b = msg2['info']
            name_b = _string_to_bytes(info_b['name'])

            g_ab_mod_m = compute_dh_key(exp, info_b['g_x_mod_m'], m)

            # assemble Bob's public key
            pubkey_b = rsa.PublicKey(info_b['n'], info_b['e'])

            ## step 2
            # H= h256(Alice, Bob,         R A ,        R B ,               g a mod m,  g b mod m, g ab mod m)
            H = h256(name, name_b, r_challenge, info_b['r_challenge'], g_x_mod_m, info_b['g_x_mod_m'], g_ab_mod_m)

            ## step 3 verificying secret
            S_b_signature = msg2['S'].strip(b'\x00')
            S_b = H + name_b
            rsa.verify(S_b, S_b_signature, pubkey_b)

            # build key
            K = h256(g_ab_mod_m)

            ## destroy a:
            print('destroying exponent a:', exp)
            del exp

            ##############
            # send msg 3 #
            ##############
            S_a = H + name
            S_a_signature = rsa.sign(S_a, privkey, 'SHA-256')

            msg3_payload = name + S_a_signature
            msg3_ciphertext = CipherLib.aes(msg3_payload, key=K)

            msg3 = {
                'seq': 3,
                'payload': msg3_ciphertext,
            }
            print('auth: sending msg #3', list(msg3.keys()))

            # sending E(Alice, S_A ,)
            print('sending msg3:', msg3)
            send_msg(conn, args2msg(msg3))

            return K

    else:  # if server (Bob)

        ##############
        # recv msg 1 #
        ##############

        # changing key for testing, auth should fail
        if 'test' in args and args['test']==1:
            privkey.d -= 1
        

        # client has already sent the stuff
        msg1 = args['msg1']
        assert args['seq'] == 1
        print('auth: received msg1', list(msg1.keys()))

        name_a = _string_to_bytes(msg1['name'])
        g_ab_mod_m = compute_dh_key(exp, msg1['g_x_mod_m'], m)

        # assemble Alice's public key
        pubkey_a = rsa.PublicKey(msg1['n'], msg1['e'])

        ##############
        # send msg 2 #
        ##############
        # H = h 256 (Alice, Alice, R A , R B , g a mod m, g b mod m, g ab mod m)
        H = h256(name_a, name, msg1['r_challenge'], r_challenge, msg1['g_x_mod_m'], g_x_mod_m, g_ab_mod_m)

        S_b = H + name
        S_b_signature = rsa.sign(S_b, privkey, 'SHA-256')

        K = h256(g_ab_mod_m)

        # R_B , g b mod m, S B
        # this was prepared in the beginning of this function (after init DH)
        msg2 = {
            'seq': 2,
            'S': S_b_signature,
            'info': init_info,
        }
        print('sending msg2:', msg2)
        send_msg(conn, args2msg(msg2))

        ##############
        # recv msg 3 #
        ##############
        msg3_container = msg2args(recv_msg(conn))
        assert msg3_container['seq'] == 3
        msg3_ciphertext = msg3_container['payload']

        msg3 = CipherLib.aes(msg3_ciphertext, decrypt=True, key=K)

        ## verifying secret
        S_a_signature = msg3[len(name_a):].strip(b'\x00')
        S_a = (H + name_a)
        try:
            rsa.verify(S_a, S_a_signature, pubkey_a)
        except rsa.VerificationError as e:
            print('AUTHENTICATION FAILED!! S_a did not match signature:\n',
                  S_a_signature, ' is not the signature of ', S_a)
            return False

        ## destroy b:
        print('destroying exponent b:', exp)
        del exp

        return K


def h256(*args):
    sha256 = hashlib.sha256()

    for arg in args:
        if isinstance(arg, int):
            arg = int_to_bytes(arg)
        if isinstance(arg, str):
            arg = _string_to_bytes(arg)
        sha256.update(arg)

    return sha256.digest()


def init_DiffieHellman():
    g = 2
    m = int_from_bytes(b''.join(
        [b'FFFFFFFF', b'FFFFFFFF', b'C90FDAA2', b'2168C234', b'C4C6628B', b'80DC1CD1', b'29024E08', b'8A67CC74',
         b'020BBEA6', b'3B139B22', b'514A0879', b'8E3404DD', b'EF9519B3', b'CD3A431B', b'302B0A6D', b'F25F1437',
         b'4FE1356D', b'6D51C245', b'E485B576', b'625E7EC6', b'F44C42E9', b'A637ED6B', b'0BFF5CB6', b'F406B7ED',
         b'EE386BFB', b'5A899FA5', b'AE9F2411', b'7C4B1FE6', b'49286651', b'ECE45B3D', b'C2007CB8', b'A163BF05',
         b'98DA4836', b'1C55D39A', b'69163FA8', b'FD24CF5F', b'83655D23', b'DCA3AD96', b'1C62F356', b'208552BB',
         b'9ED52907', b'7096966D', b'670C354E', b'4ABC9804', b'F1746C08', b'CA18217C', b'32905E46', b'2E36CE3B',
         b'E39E772C', b'180E8603', b'9B2783A2', b'EC07A28F', b'B5C55DF0', b'6F4C52C9', b'DE2BCBF6', b'95581718',
         b'3995497C', b'EA956AE5', b'15D22618', b'98FA0510', b'15728E5A', b'8AACAA68', b'FFFFFFFF', b'FFFFFFFF']))
    exp = int_from_bytes(secrets.token_bytes(2048 // 8))
    return exp, g, m


def init_asym_key(is_client):
    if is_client:
        p = 3136666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666313
        q = 3130000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001183811000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000313

        p1q1 = 9817766666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666670379887169999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999868533333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333332913475031999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999889344
        n = 9817766666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666670379887169999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999874799999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999581325509666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666555969
    else:
        p = 262641725682127839334668938847190331798311145333616792958372838424857156775007227102454928148183167823211534641943299795962309579874682913568608650959193370824474863282145037585560618568778906679404993323367715662527874977471424467472818616772123866421714232029284828476022113987781717658486369598393166193032285497153837454766280540159
        q = 1357911131517193133353739515355575971737577799193959799111113115117119131133135137139151153155157159171173175177179191193195197199311313315317319331333335337339351353355357359371373375377379391393395397399511513515517519531533535537539551553555557559571573575577579591593595597599711713715717719731733735737739751753755757759771

        p1q1 = 356644122904646457852499602347524156507174390136009247712353815755646024496037172622143518964975128825130286514080704742796667108474987831191018350950474273866002102276256204821917798997344429811579551036427931632160027755615469206884341989791425882965139555633729680961753531307429384131685187536265971374229677283297296199726262570199844444846074490909237009199214584948274744025059837855042663253503317322749974093852969723202432993253172732373126211278665570242752797366587342079290772234755716489053248405176862032307451968502682676607826140044221793217557204694793133501557346193212066671570792229108422899589042187213282710832047367190550286939155601843660
        n = 356644122904646457852499602347524156507174390136009247712353815755646024496037172622143518964975128825130286514080704742796667108474987831191018350950474273866002102276256204821917798997344429811579551036427931632160027755615469206884341989791425882965139555633729680961753531307429384131685187536265971374229677283297296199726525211926884483816926352981437939046368472065345938617212170492578633525395443680985564159140304044180801687066289207346267712051735450355632719332863854781448582435377212879994166383117014314364236353219445789669865528537210737216563558849104808921534617984812925075624393934689800214847240270527393596756813388425443876147677640143589

    start_time = time.time()
    # p1q1 = (p - 1) * (q - 1)
    # n = p * q
    e = find_coprime(p1q1)
    d = modinv(p1q1, n)

    print(f'Initialized RSA in: {time.time() - start_time}sec')
    return n, e, d, q, p


def compute_dh_key(s_exp, other_g_x_mod_m, m):
    """
    :returns the combined symmetric key
    """
    return exp_mod(other_g_x_mod_m, s_exp, m)


def exp_mod(bas, exp, n):
    """
    find $(bas ** exp) % n$

    :param base:
    :param exp:
    :param n: modulous

    taken form https://www.geeksforgeeks.org/exponential-squaring-fast-modulo-multiplication/
    """
    t = 1
    while (exp > 0):
        # for cases where exponent
        # is not an even value
        if (exp % 2 != 0):
            t = (t * bas) % n

        bas = (bas * bas) % n
        exp = exp // 2
    return t % n

def decode_base64(data, altchars=b'+/'):
    """Decode base64, padding being optional.

    :param data: Base64 data as an ASCII byte string
    :returns: The decoded byte string.

    """
    data = re.sub(rb'[^a-zA-Z0-9%s]+' % altchars, b'', data)  # normalize
    missing_padding = len(data) % 4
    if missing_padding:
        data += b'='* (4 - missing_padding)
    return base64.b64decode(data, altchars)