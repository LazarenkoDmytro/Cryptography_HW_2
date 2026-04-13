"""
Brute-force S_12_hi (upper 32 bits of S_12) with multiprocessing + numpy.
Guess: R1_0, R2_0, S_11, S_13, S_14, S_15, S_12_lo (416 bits)
"""

import time
import multiprocessing as mp
import numpy as np
from strumok import init, _u64, alpha_mul, alphainv_mul, transform_t, keystream_word, next_state
from strumok_tables import T0, T1, T2, T3, T4, T5, T6, T7, ALPHA_MUL, ALPHAINV_MUL

U64 = np.uint64
MASK = U64(0xFFFFFFFFFFFFFFFF)

T_TABLES = [np.array(t, dtype=np.uint64) for t in [T0, T1, T2, T3, T4, T5, T6, T7]]
ALPHA_TABLE = np.array(ALPHA_MUL, dtype=np.uint64)
ALPHAINV_TABLE = np.array(ALPHAINV_MUL, dtype=np.uint64)


def vec_alpha(x):
    return ((x << U64(8)) & MASK) ^ ALPHA_TABLE[(x >> U64(56)).astype(np.uint8)]


def vec_alphainv(x):
    return (x >> U64(8)) ^ ALPHAINV_TABLE[(x & U64(0xFF)).astype(np.uint8)]


def vec_transform_t(x):
    result = np.zeros(len(x), dtype=np.uint64)
    for i in range(8):
        byte_i = ((x >> U64(8 * i)) & U64(0xFF)).astype(np.uint8)
        result ^= T_TABLES[i][byte_i]
    return result


def worker(args):
    _, lo, hi, s12_lo, c17, S_pre, R1_pre, R2_pre, ks, queue = args
    CHUNK = 1 << 18
    s12_lo_np = U64(s12_lo)
    c17_np = U64(c17)
    checkpoint = lo + max(1 << 24, (hi - lo) // 20)

    for base in range(lo, hi, CHUNK):
        n = min(CHUNK, hi - base)
        hi_vals = np.arange(base, base + n, dtype=np.uint64)
        candidates = (hi_vals << U64(32)) | s12_lo_np

        S = {k: U64(v) for k, v in S_pre.items()}
        R1 = {k: U64(v) for k, v in R1_pre.items()}
        R2 = {k: U64(v) for k, v in R2_pre.items()}
        S[12] = candidates
        S[17] = c17_np ^ vec_alphainv(candidates)

        for t in range(2, 5):
            fsm_out = ((S[t + 15] + R1[t]) & MASK) ^ R2[t]
            S[t] = U64(ks[t]) ^ fsm_out
            S[t + 16] = vec_alpha(S[t]) ^ vec_alphainv(S[t + 11]) ^ S[t + 13]

        R1[5] = (R2[4] + S[17]) & MASK

        for t in range(5, 11):
            r1t = R1[t]
            fsm_out = ((S[t + 15] + r1t) & MASK) ^ R2[t]
            S[t] = U64(ks[t]) ^ fsm_out
            if isinstance(r1t, np.ndarray):
                R2[t + 1] = vec_transform_t(r1t)
            else:
                R2[t + 1] = U64(transform_t(int(r1t)))
            R1[t + 1] = (R2[t] + S[t + 13]) & MASK
            S[t + 16] = vec_alpha(S[t]) ^ vec_alphainv(S[t + 11]) ^ S[t + 13]

        z11 = ((S[26] + R1[11]) & MASK) ^ R2[11] ^ S[11]
        match = np.where(z11 == U64(ks[11]))[0]
        if len(match):
            return int(hi_vals[match[0]]), base - lo + n

        if base >= checkpoint:
            queue.put((base - lo,))
            checkpoint = base + max(1 << 24, (hi - lo) // 20)

    return None, hi - lo


def search(s_init, r1, r2, ks, n_workers=None):
    n_workers = n_workers or mp.cpu_count()
    s12 = s_init[12]
    s12_lo = s12 & 0xFFFFFFFF

    S = {11: s_init[11], 13: s_init[13], 14: s_init[14], 15: s_init[15]}
    R1, R2 = {0: r1}, {0: r2}

    S[0] = ks[0] ^ (_u64(S[15] + R1[0]) ^ R2[0])
    R2[1] = transform_t(R1[0])
    R1[1] = _u64(R2[0] + S[13])
    S[16] = alpha_mul(S[0]) ^ alphainv_mul(S[11]) ^ S[13]

    S[1] = ks[1] ^ (_u64(S[16] + R1[1]) ^ R2[1])
    R2[2] = transform_t(R1[1])
    R1[2] = _u64(R2[1] + S[14])

    R2[3] = transform_t(R1[2])
    R1[3] = _u64(R2[2] + S[15])
    R2[4] = transform_t(R1[3])
    R1[4] = _u64(R2[3] + S[16])
    R2[5] = transform_t(R1[4])

    c17 = alpha_mul(S[1]) ^ S[14]

    total = 1 << 32
    per_worker = total // n_workers
    mgr = mp.Manager()
    queue = mgr.Queue()
    tasks = [
        (i, i * per_worker, (i + 1) * per_worker if i < n_workers - 1 else total,
         s12_lo, c17, dict(S), dict(R1), dict(R2), list(ks), queue)
        for i in range(n_workers)
    ]

    print(f"searching 2^32 candidates, {n_workers} workers")
    t0 = time.time()
    with mp.Pool(n_workers) as pool:
        results = pool.map(worker, tasks)

    dt = time.time() - t0
    found = next((r for r, _ in results if r is not None), None)
    checked = sum(c for _, c in results)
    print(f"done in {dt:.1f}s, {checked / dt / 1e6:.1f}M/s")

    if found is not None:
        got = (found << 32) | s12_lo
        print(f"S_12 = 0x{got:016X}  {'ok' if got == s12 else 'WRONG'}")
        return found
    return None


if __name__ == "__main__":
    s, r1, r2 = init(bytes(range(64)), bytes(range(32)))
    st, r1t, r2t = list(s), r1, r2
    ks = []
    for _ in range(17):
        ks.append(keystream_word(st, r1t, r2t))
        st, r1t, r2t = next_state(st, r1t, r2t)
    search(s, r1, r2, ks)
