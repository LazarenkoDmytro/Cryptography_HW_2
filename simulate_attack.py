import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from strumok import init, keystream_word, next_state, alpha_mul, alphainv_mul, transform_t

KEY = bytes.fromhex(
    "8000000000000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000"
)
IV = bytes.fromhex("0000000000000000000000000000000000000000000000000000000000000000")

TICKS = 11
GUESSED = ['R2_8', 'R2_9', 'w_9', 'R2_10', 'R1_10', 'w_10', 'R1_11']
mask64 = lambda x: x & 0xFFFFFFFFFFFFFFFF

def run_cipher():
    lfsr, r1, r2 = init(KEY, IV)
    w = {i: lfsr[i] for i in range(16)}
    R1, R2, keystream = {}, {}, {}

    for t in range(TICKS):
        R1[t], R2[t] = r1, r2
        keystream[t] = keystream_word(lfsr, r1, r2)
        prev = list(lfsr)
        lfsr, r1, r2 = next_state(lfsr, r1, r2)
        w[t + 16] = alpha_mul(prev[0]) ^ alphainv_mul(prev[11]) ^ prev[13]
    R1[TICKS], R2[TICKS] = r1, r2
    return w, R1, R2, keystream

def get_guessed_values(w, R1, R2):
    known = {}
    for name in GUESSED:
        kind, idx = name.split('_')
        idx = int(idx)
        known[name] = {'w': w, 'R1': R1, 'R2': R2}[kind][idx]
    return known

def build_inv_T(R1, R2):
    return {R2[t + 1]: R1[t] for t in range(TICKS)}

def propagate(known, keystream, inv_T):
    def get(name):
        return known.get(name)

    def save(name, value):
        if name not in known:
            known[name] = value
            print(f"  {name} = {value:016x}")

    while True:
        count = len(known)

        for t in range(TICKS):
            wt   = f'w_{t}'
            wt11 = f'w_{t+11}'
            wt13 = f'w_{t+13}'
            wt15 = f'w_{t+15}'
            wt16 = f'w_{t+16}'
            R1t  = f'R1_{t}'
            R2t  = f'R2_{t}'
            R1t1 = f'R1_{t+1}'
            R2t1 = f'R2_{t+1}'

            a, b, c, d = get(wt), get(wt11), get(wt13), get(wt16)

            if a and b and c:
                save(wt16, alpha_mul(a) ^ alphainv_mul(b) ^ c)
            if b and c and d:
                save(wt, alphainv_mul(d ^ alphainv_mul(b) ^ c))
            if a and c and d:
                save(wt11, alpha_mul(d ^ alpha_mul(a) ^ c))
            if a and b and d:
                save(wt13, d ^ alpha_mul(a) ^ alphainv_mul(b))

            r1_cur, r2_next = get(R1t), get(R2t1)
            if r1_cur:
                save(R2t1, transform_t(r1_cur))
            if r2_next and r2_next in inv_T:
                save(R1t, inv_T[r2_next])

            r1_next, r2_cur, w13 = get(R1t1), get(R2t), get(wt13)
            if r2_cur and w13:
                save(R1t1, mask64(r2_cur + w13))
            if r1_next and w13:
                save(R2t, mask64(r1_next - w13))
            if r1_next and r2_cur:
                save(wt13, mask64(r1_next - r2_cur))

            z = keystream[t]
            w0, w15, r1, r2 = get(wt), get(wt15), get(R1t), get(R2t)

            if w15 and r1 and r2:
                save(wt, mask64(mask64(w15 + r1) ^ r2 ^ z))
            if w0 and r1 and r2:
                save(wt15, mask64(mask64(z ^ r2 ^ w0) - r1))
            if w0 and w15 and r1:
                save(R2t, mask64(mask64(w15 + r1) ^ z ^ w0))
            if w0 and w15 and r2:
                save(R1t, mask64(mask64(z ^ r2 ^ w0) - w15))

        if len(known) == count:
            break
    return known


def verify(recovered, w, R1, R2):
    truth = {f'w_{i}': w[i] for i in range(27) if i in w}
    truth.update({f'R1_{t}': R1[t] for t in range(TICKS + 1)})
    truth.update({f'R2_{t}': R2[t] for t in range(TICKS + 1)})
    result = sum(1 for name, val in truth.items() if recovered.get(name) == val)
    return result, len(truth)


def main():
    print("Full cipher state collection")
    w, R1, R2, keystream = run_cipher()

    print("\nKnown keystream words:")
    for t in range(TICKS):
        print(f"z_{t} = {keystream[t]:016x}")

    known = get_guessed_values(w, R1, R2)
    print(f"\nGuessed values ({len(known)}):")
    for name, value in known.items():
        print(f"{name} = {value:016x}")

    print("\nRunning propagation")
    inv_T = build_inv_T(R1, R2)
    recovered = propagate(known, keystream, inv_T)

    print("\nVerification")
    recovered_count, total_count = verify(recovered, w, R1, R2)
    print(f"Recovered variables: {recovered_count}/{total_count}")

    if recovered_count == total_count:
        print("Recovery completed successfully.")
    else:
        print("Recovery is incomplete.")


if __name__ == '__main__':
    main()