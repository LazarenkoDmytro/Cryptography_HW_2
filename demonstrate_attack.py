"""
6-guess attack on Strumok-512: guess R1_0, R2_0, S_11, S_13, S_14, S_15
and show that S_12 is uniquely determined by the keystream.
"""

import random
from strumok import (
    alpha_mul, alphainv_mul, transform_t,
    init, next_state, keystream_word, _u64,
)


def propagate(s12, guessed_s, r1, r2, ks, ticks):
    S = {**guessed_s, 12: s12}
    R1, R2 = {0: r1}, {0: r2}
    checks = []

    for t in range(ticks):
        fsm = _u64(S[t+15] + R1[t]) ^ R2[t]
        if t in S:
            checks.append((fsm ^ S[t], ks[t]))
        else:
            S[t] = ks[t] ^ fsm
        R2[t+1] = transform_t(R1[t])
        R1[t+1] = _u64(R2[t] + S[t+13])
        S[t+16] = alpha_mul(S[t]) ^ alphainv_mul(S[t+11]) ^ S[t+13]

    return S, checks


if __name__ == "__main__":
    s_init, r1, r2 = init(bytes(range(64)), bytes(range(32)))

    ks = []
    s, r1t, r2t = list(s_init), r1, r2
    for _ in range(17):
        ks.append(keystream_word(s, r1t, r2t))
        s, r1t, r2t = next_state(s, r1t, r2t)

    guessed = {11: s_init[11], 13: s_init[13], 14: s_init[14], 15: s_init[15]}

    print("6-guess attack: R1_0, R2_0, S_11, S_13, S_14, S_15 (384 bits)")
    print(f"unknown: S_12\n")

    S, checks = propagate(s_init[12], guessed, r1, r2, ks, 13)
    ok = all(a == b for a, b in checks)
    state_ok = all(S[i] == s_init[i] for i in range(16))
    print(f"correct S_12: checks {sum(a==b for a,b in checks)}/{len(checks)}, state {'ok' if state_ok else 'FAIL'}")

    rng = random.Random(42)
    for _ in range(5):
        w = rng.getrandbits(64)
        _, wc = propagate(w, guessed, r1, r2, ks, 13)
        print(f"wrong   S_12=0x{w:016X}: {sum(a!=b for a,b in wc)}/{len(wc)} checks failed")

    print(f"\ntotal complexity: 2^384 * 2^64 = 2^448")
