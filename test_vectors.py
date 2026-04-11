import time
from strumok import strumok

VECTORS_256 = {
    "256-bit #1 (K=8000.., IV=0)": (
        "80000000000000000000000000000000"
        "00000000000000000000000000000000",
        "00000000000000000000000000000000"
        "00000000000000000000000000000000",
        [
            0xe442d15345dc66ca, 0xf47d700ecc66408a,
            0xb4cb284b5477e641, 0xa2afc9092e4124b0,
            0x728e5fa26b11a7d9, 0xe6a7b9288c68f972,
            0x70eb3606de8ba44c, 0xaced7956bd3e3de7,
        ],
    ),
    "256-bit #2 (K=AAAA.., IV=0)": (
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "00000000000000000000000000000000"
        "00000000000000000000000000000000",
        [
            0xa7510b38c7a95d1d, 0xcd5ea28a15b8654f,
            0xc5e2e2771d0373b2, 0x98ae829686d5fcee,
            0x45bddf65c523dbb8, 0x32a93fcdd950001f,
            0x752a7fb588af8c51, 0x9de92736664212d4,
        ],
    ),
    "256-bit #3 (K=8000.., IV=4,3,2,1)": (
        "80000000000000000000000000000000"
        "00000000000000000000000000000000",
        "00000000000000040000000000000003"
        "00000000000000020000000000000001",
        [
            0xfe44a2508b5a2acd, 0xaf355b4ed21d2742,
            0xdcd7fdd6a57a9e71, 0x5d267bd2739fb5eb,
            0xb22eee96b2832072, 0xc7de6a4cdaa9a847,
            0x72d5da93812680f2, 0x4a0acb7e93da2ce0,
        ],
    ),
    "256-bit #4 (K=AAAA.., IV=4,3,2,1)": (
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "00000000000000040000000000000003"
        "00000000000000020000000000000001",
        [
            0xe6d0efd9cea5abcd, 0x1e78ba1a9b0e401e,
            0xbcfbea2c02ba0781, 0x1bd375588ae08794,
            0x5493cf21e114c209, 0x66cd5d7cc7d0e69a,
            0xa5cdb9f3380d07fa, 0x2940d61a4d4e9ce4,
        ],
    ),
}

VECTORS_512 = {
    "512-bit #1 (K=8000.., IV=0)": (
        "80000000000000000000000000000000"
        "00000000000000000000000000000000"
        "00000000000000000000000000000000"
        "00000000000000000000000000000000",
        "00000000000000000000000000000000"
        "00000000000000000000000000000000",
        [
            0xf5b9ab51100f8317, 0x898ef2086a4af395,
            0x59571fecb5158d0b, 0xb7c45b6744c71fbb,
            0xff2efcf05d8d8db9, 0x7a585871e5c419c0,
            0x6b5c4691b9125e71, 0xa55be7d2b358ec6e,
        ],
    ),
    "512-bit #2 (K=AAAA.., IV=0)": (
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "00000000000000000000000000000000"
        "00000000000000000000000000000000",
        [
            0xd2a6103c50bd4e04, 0xdc6a21af5eb13b73,
            0xdf4ca6cb07797265, 0xf453c253d8d01876,
            0x039a64dc7a01800c, 0x688ce327dccb7e84,
            0x41e0250b5e526403, 0x9936e478aa200f22,
        ],
    ),
    "512-bit #3 (K=8000.., IV=4,3,2,1)": (
        "80000000000000000000000000000000"
        "00000000000000000000000000000000"
        "00000000000000000000000000000000"
        "00000000000000000000000000000000",
        "00000000000000040000000000000003"
        "00000000000000020000000000000001",
        [
            0xcca12eae8133aaaa, 0x528d85507ce8501d,
            0xda83c7fe3e1823f1, 0x21416ebf63b71a42,
            0x26d76d2bf1a625eb, 0xeec66ee0cd0b1efc,
            0x02dd68f338a345a8, 0x47538790a5411adb,
        ],
    ),
    "512-bit #4 (K=AAAA.., IV=4,3,2,1)": (
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "00000000000000040000000000000003"
        "00000000000000020000000000000001",
        [
            0x965648e775c717d5, 0xa63c2a7376e92df3,
            0x0b0eb0bbd47ca267, 0xea593d979ae5bd39,
            0xd773b5e5193cafe1, 0xb0a26671d259422b,
            0x85b2aa326b280156, 0x511ace6451435f0c,
        ],
    ),
}


def check(label, output, expected):
    if output == expected:
        print(f"  ok   {label}")
        return True
    print(f"  FAIL {label}")
    for i, (got, exp) in enumerate(zip(output, expected)):
        if got != exp:
            print(f"       Z{i}: got {got:016x}, want {exp:016x}")
    return False


def run_tests():
    passed = 0
    total = 0

    print("--- strumok-256 ---")
    for label, (key_hex, iv_hex, expected) in VECTORS_256.items():
        key = bytes.fromhex(key_hex)
        iv = bytes.fromhex(iv_hex)
        output = strumok(key, iv, num_words=8)
        if check(label, output, expected):
            passed += 1
        total += 1

    print("--- strumok-512 ---")
    for label, (key_hex, iv_hex, expected) in VECTORS_512.items():
        key = bytes.fromhex(key_hex)
        iv = bytes.fromhex(iv_hex)
        output = strumok(key, iv, num_words=8)
        if check(label, output, expected):
            passed += 1
        total += 1

    print(f"\n{passed}/{total} tests passed")
    return passed == total


def run_benchmark():
    n = 100_000

    key_hex_256, iv_hex, _ = list(VECTORS_256.values())[0]
    key_hex_512, _, _ = list(VECTORS_512.values())[0]

    key_256 = bytes.fromhex(key_hex_256)
    key_512 = bytes.fromhex(key_hex_512)
    iv = bytes.fromhex(iv_hex)

    size_kb = n * 8 / 1024

    print(f"\nbenchmark: {n} words ({size_kb:.0f} KB)")

    t0 = time.perf_counter()
    strumok(key_256, iv, num_words=n)
    dt = time.perf_counter() - t0
    print(f"  256-bit: {dt:.3f}s, {n * 8 / dt / 1e6:.1f} MB/s")

    t0 = time.perf_counter()
    strumok(key_512, iv, num_words=n)
    dt = time.perf_counter() - t0
    print(f"  512-bit: {dt:.3f}s, {n * 8 / dt / 1e6:.1f} MB/s")


if __name__ == "__main__":
    import sys

    ok = run_tests()
    run_benchmark()
    sys.exit(0 if ok else 1)
