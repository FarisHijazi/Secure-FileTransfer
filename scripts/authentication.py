import json
import socket

from client_backend import format_args_to_json
from byte_utils import _string_to_bytes, _bytes_to_string, int_to_bytes, int_from_bytes
from utils import send_msg, recv_msg, AttrDict, modinv, find_coprime
import time


def authenticate(args, is_client=True, conn=None):
    p, q, N, e, d = init_asym_key(is_client)

    if is_client:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            print('connecting to server...', end='')
            s.connect((args.host, args.port))  # connect
            print('\rConnection established                       ')

            request_json = format_args_to_json(args)

            # send the command/request json
            send_msg(s, _string_to_bytes(request_json))

            # check if server acknowledged the command
            # (if resp is included in one of the success response codes)
            resp = recv_msg(s)
            resp_json = AttrDict(json.loads(_bytes_to_string(resp)))
            if resp_json.readystate in [202]:
                send_msg(s, b'200')  # send OK code
                print('\nTransaction complete')


def init_asym_key(is_client):
    if is_client:
        p = 3136666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666313
        q = 3130000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001183811000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000313
        # p1q1 = 9817766666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666670379887169999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999868533333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333333332913475031999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999889344
        # N = 9817766666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666670379887169999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999874799999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999581325509666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666555969
    else:
        p = 262641725682127839334668938847190331798311145333616792958372838424857156775007227102454928148183167823211534641943299795962309579874682913568608650959193370824474863282145037585560618568778906679404993323367715662527874977471424467472818616772123866421714232029284828476022113987781717658486369598393166193032285497153837454766280540159
        q = 1357911131517193133353739515355575971737577799193959799111113115117119131133135137139151153155157159171173175177179191193195197199311313315317319331333335337339351353355357359371373375377379391393395397399511513515517519531533535537539551553555557559571573575577579591593595597599711713715717719731733735737739751753755757759771
        # p1q1 = 356644122904646457852499602347524156507174390136009247712353815755646024496037172622143518964975128825130286514080704742796667108474987831191018350950474273866002102276256204821917798997344429811579551036427931632160027755615469206884341989791425882965139555633729680961753531307429384131685187536265971374229677283297296199726262570199844444846074490909237009199214584948274744025059837855042663253503317322749974093852969723202432993253172732373126211278665570242752797366587342079290772234755716489053248405176862032307451968502682676607826140044221793217557204694793133501557346193212066671570792229108422899589042187213282710832047367190550286939155601843660
        # N = 356644122904646457852499602347524156507174390136009247712353815755646024496037172622143518964975128825130286514080704742796667108474987831191018350950474273866002102276256204821917798997344429811579551036427931632160027755615469206884341989791425882965139555633729680961753531307429384131685187536265971374229677283297296199726525211926884483816926352981437939046368472065345938617212170492578633525395443680985564159140304044180801687066289207346267712051735450355632719332863854781448582435377212879994166383117014314364236353219445789669865528537210737216563558849104808921534617984812925075624393934689800214847240270527393596756813388425443876147677640143589

    start_time = time.time()
    p1q1 = (p - 1) * (q - 1)
    N = p * q
    e = find_coprime(p1q1)
    d = modinv(p1q1, N)
    print(
        f'Initialized RSA:'
        f'\ne={e}'
        f'\nd={d}'
        f'\ntime taken: {time.time() - start_time}sec'
    )
    return p, q, N, e, d
