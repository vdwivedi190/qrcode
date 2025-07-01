"""
This modules contains functions to perform arithmetic operations in the Galois field
GF(2) and GF(2^8). These operations are used in the Reed-Solomon error correction
algorithm in the QR code standard.

"""

# Generator for the Galois field GF(2^8). The bits in the binary representation of 285
# are interpreted as the coefficients of the polynomial over GF(2)
GALOIS_GEN = 285


# GENERATE THE LOG AND ANTILOG TABLES ON GF(2^8)
# =============================================


def gen_GF_log_tables() -> tuple[dict[int, int], dict[int, int]]:
    """Generates the log and antilog tables for the Galois field GF(2^8)."""
    GF_antilogs: dict[int, int] = {}

    num = 1
    GF_antilogs[0] = num

    for i in range(1, 255):
        num *= 2
        if num > 255:
            num ^= GALOIS_GEN  # Reduce modulo the generator polynomial
        GF_antilogs[i] = num

    # Invert the dictionary to get the logs
    GF_logs = {val: key for key, val in GF_antilogs.items()}

    return GF_logs, GF_antilogs


# Generate the log and antilog tables for the Galois field GF(2^8)
GF_logs, GF_antilogs = gen_GF_log_tables()


# ARITHEMETIC OPERATIONS IN GF(2^8)
# =============================================


def GF_mult(x: int, y: int) -> int:
    """Multiply two values in the Galois field GF(2^8) using precomputed log tables."""
    if x == 0 or y == 0:
        return 0
    else:
        return GF_antilogs[(GF_logs[x] + GF_logs[y]) % 255]


def GF_div(x: int, y: int) -> int:
    """Divide two values in the Galois field GF(2^8) using precomputed log tables."""
    if x == 0:
        return 0
    elif y == 0:
        raise ZeroDivisionError("Division by zero in Galois field GF(2^8)!")
    else:
        return GF_antilogs[(GF_logs[x] - GF_logs[y]) % 255]


def GF_mult_poly(poly1: list[int], poly2: list[int]) -> list[int]:
    """Multiply two polynomials in the Galois field GF(2^8)."""

    # Compute the lengths of the given polynomials and their product
    nterms1 = len(poly1)
    nterms2 = len(poly2)
    nterms = nterms1 + nterms2 - 1

    # Initialize an array to store the product
    prod = [0] * nterms
    for i in range(nterms):
        jmin = max(0, i - nterms2 + 1)
        jmax = min(i, nterms1 - 1)
        for j in range(jmin, jmax + 1):
            prod[i] ^= GF_mult(poly1[j], poly2[i - j])
    return prod


# TODO: Return both quotient and remainder and choose the one that is needed in the caller
def GF_div_poly(poly1: list[int], poly2: list[int]) -> list[int]:
    """Divide two polynomials in the Galois field GF(2^8).

    Returns the remainder of the division."""

    # Compute the lengths of the given polynomials and the product
    nterms1 = len(poly1)
    nterms2 = len(poly2)

    # If the dividend has fewer terms than the divisor, then the entire dividend is the remainder
    if nterms1 < nterms2:
        return poly1

    nterms = nterms1 - nterms2
    ptmp = poly1.copy()

    # Initialize an array to store the product
    for i in range(nterms + 1):
        if ptmp[i] == 0:
            continue

        fact = GF_div(ptmp[i], poly2[0])
        for j in range(nterms2):
            ptmp[i + j] ^= GF_mult(poly2[j], fact)

    return ptmp[-nterms2 + 1 :]
