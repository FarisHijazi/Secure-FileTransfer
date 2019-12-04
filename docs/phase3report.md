# Phase 2 report

## Requirements

Including authentication

## Implementation details

For the prime numbers, I'll be using the following:

### Client

p = 313 6666666666 6666666666 6666666666
6666666666 6666666666 6666666666 6666666666 6666666666 6666666666 6666666666
6666666666 6666666666 6666666666 6666666666 6666666666 6666666666 6666666666
6666666666 6666666666 6666666666 6666666666 6666666666 6666666666 6666666666
6666666666 6666666666 6666666666 6666666666 6666666666 6666666666 6666666313
q = 313 0000000000 0000000000 0000000000
0000000000 0000000000 0000000000 0000000000 0000000000 0000000000 0000000000
0000000000 0000000000 0000000000 0000000000 0000000000 1183811000 0000000000
0000000000 0000000000 0000000000 0000000000 0000000000 0000000000 0000000000
0000000000 0000000000 0000000000 0000000000 0000000000 0000000000 0000000313

which have been acquired from these links:

- https://primes.utm.edu/curios/page.php?number_id=10421
- https://primes.utm.edu/curios/page.php?number_id=162

### Server

p = 262641 7256821278 3933466893 8847190331 7983111453 3361679295
8372838424 8571567750 0722710245 4928148183 1678232115 3464194329 9795962309
5798746829 1356860865 0959193370 8244748632 8214503758 5560618568 7789066794
0499332336 7715662527 8749774714 2446747281 8616772123 8664217142 3202928482
8476022113 9877817176 5848636959 8393166193 0322854971 5383745476 6280540159

q = 13579111 3151719313 3353739515 3555759717 3757779919
3959799111 1131151171 1913113313 5137139151 1531551571 5917117317 5177179191
1931951971 9931131331 5317319331 3333353373 3935135335 5357359371 3733753773
7939139339 5397399511 5135155175 1953153353 5537539551 5535555575 5957157357
5577579591 5935955975 9971171371 5717719731 7337357377 3975175375 5757759771

which have been acquired from these links:

- https://primes.utm.edu/curios/page.php?number_id=3183
- https://primes.utm.edu/curios/page.php?number_id=10319

For the cryptographically secure random number generation,
I'm using python's [secrets](https://docs.python.org/3/library/secrets.html) library.

## Assignment details

The code changes made for phase 2 can be found on GitHub, the branch [ph2-encryption](https://github.com/FarisHijazi/Secure-FileTransfer/tree/ph2-encryption). You can see the code changes made on [this page](https://github.com/FarisHijazi/Secure-FileTransfer/commits/ph2-encryption).