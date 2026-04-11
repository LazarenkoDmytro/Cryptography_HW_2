from strumok_tables import (
    T0, T1, T2, T3, T4, T5, T6, T7,
    ALPHA_MUL, ALPHAINV_MUL,
)

VALID_KEY_SIZES = (32, 64)
IV_SIZE = 32


def _u64(x):
    return x & 0xFFFFFFFFFFFFFFFF


def _bytes_to_words(data):
    return [int.from_bytes(data[i:i + 8], "big") for i in range(0, len(data), 8)]


def _validate_key(key):
    if not isinstance(key, (bytes, bytearray)):
        raise TypeError("key must be bytes")
    if len(key) not in VALID_KEY_SIZES:
        raise ValueError(f"bad key size: {len(key)} bytes, need 32 or 64")


def _validate_iv(iv):
    if not isinstance(iv, (bytes, bytearray)):
        raise TypeError("iv must be bytes")
    if len(iv) != IV_SIZE:
        raise ValueError(f"bad iv size: {len(iv)} bytes, need {IV_SIZE}")


def alpha_mul(x):
    return _u64(x << 8) ^ ALPHA_MUL[x >> 56]


def alphainv_mul(x):
    return (x >> 8) ^ ALPHAINV_MUL[x & 0xFF]


def transform_t(x):
    return (
        T0[x & 0xFF]
        ^ T1[(x >> 8) & 0xFF]
        ^ T2[(x >> 16) & 0xFF]
        ^ T3[(x >> 24) & 0xFF]
        ^ T4[(x >> 32) & 0xFF]
        ^ T5[(x >> 40) & 0xFF]
        ^ T6[(x >> 48) & 0xFF]
        ^ T7[(x >> 56) & 0xFF]
    )


def fsm(x, y, z):
    return _u64(x + y) ^ z


def next_state(s, r1, r2, init_mode=False):
    r2_new = transform_t(r1)
    r1_new = _u64(r2 + s[13])

    feedback = alpha_mul(s[0]) ^ alphainv_mul(s[11]) ^ s[13]
    if init_mode:
        feedback ^= fsm(s[15], r1, r2)

    s_new = s[1:] + [feedback]
    return s_new, r1_new, r2_new


def keystream_word(s, r1, r2):
    return fsm(s[15], r1, r2) ^ s[0]


def _init_256(key_words, iv_words):
    K0, K1, K2, K3 = key_words[3], key_words[2], key_words[1], key_words[0]
    IV0, IV1, IV2, IV3 = iv_words[3], iv_words[2], iv_words[1], iv_words[0]

    s = [0] * 16
    s[15] = _u64(~K0)
    s[14] = K1
    s[13] = _u64(~K2)
    s[12] = K3
    s[11] = K0
    s[10] = _u64(~K1)
    s[9] = K2
    s[8] = K3
    s[7] = _u64(~K0)
    s[6] = _u64(~K1)
    s[5] = K2 ^ IV3
    s[4] = K3
    s[3] = K0 ^ IV2
    s[2] = K1 ^ IV1
    s[1] = K2
    s[0] = K3 ^ IV0

    return s


def _init_512(key_words, iv_words):
    K0 = key_words[7]
    K1 = key_words[6]
    K2 = key_words[5]
    K3 = key_words[4]
    K4 = key_words[3]
    K5 = key_words[2]
    K6 = key_words[1]
    K7 = key_words[0]
    IV0, IV1, IV2, IV3 = iv_words[3], iv_words[2], iv_words[1], iv_words[0]

    s = [0] * 16
    s[15] = K0
    s[14] = _u64(~K1)
    s[13] = K2
    s[12] = K3
    s[11] = _u64(~K7)
    s[10] = K5
    s[9] = _u64(~K6)
    s[8] = K4 ^ IV3
    s[7] = _u64(~K0)
    s[6] = K1
    s[5] = K2 ^ IV2
    s[4] = K3
    s[3] = K4 ^ IV1
    s[2] = K5
    s[1] = K6
    s[0] = K7 ^ IV0

    return s


def init(key, iv):
    _validate_key(key)
    _validate_iv(iv)

    key_words = _bytes_to_words(key)
    iv_words = _bytes_to_words(iv)

    if len(key) == 32:
        s = _init_256(key_words, iv_words)
    else:
        s = _init_512(key_words, iv_words)

    r1, r2 = 0, 0

    for _ in range(32):
        s, r1, r2 = next_state(s, r1, r2, init_mode=True)

    s, r1, r2 = next_state(s, r1, r2, init_mode=False)

    return s, r1, r2


def strumok(key, iv, num_words=8):
    s, r1, r2 = init(key, iv)

    output = []
    for _ in range(num_words):
        z = keystream_word(s, r1, r2)
        output.append(z)
        s, r1, r2 = next_state(s, r1, r2)

    return output
