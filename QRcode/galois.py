import numpy as np 
from .general import find_start

GALOIS_GEN = 285   # Generator polynomial for the Galois field GF(2^8)

# Function to generate the log and antilog tables for the Galois field GF(2^8)
def gen_GF_log_tables():
    # Initialize a dictionary to store the antilogs as n:2^n for n in 0,1,...,254
    GF_antilogs = {}
    
    num = 1
    GF_antilogs[0] = num

    for i in range(1,255):
        num *= 2
        if num > 255:
            num ^= GALOIS_GEN  # XOR with the generator polynomial
        GF_antilogs[i] = num

    # Invert the dictionary to get the logs 
    GF_logs = {val: key for key, val in GF_antilogs.items()}

    return GF_logs, GF_antilogs


# Multiplication of two values in the Galois field GF(2^8) using precomputed log tables
def GF_mult(x, y):
    if x == 0 or y == 0:
        return 0
    else:
        return GF_antilogs[(GF_logs[x] + GF_logs[y]) % 255]
    

# Division of two values in the Galois field GF(2^8) using precomputed log tables
def GF_div(x, y):
    if x == 0:
        return 0
    elif y == 0:    
        return None
    else:
        return GF_antilogs[(GF_logs[x] - GF_logs[y]) % 255]
    
    

# Multiplication of two polynomials in the Galois field GF(2^8) using precomputed log tables
def GF_mult_poly(p1, p2):
    # Compute the lengths of the given polynomials and the product 
    nterms1 = len(p1)
    nterms2 = len(p2)
    nterms = nterms1 + nterms2 - 1

    # Initialize an array to store the product
    prod = np.zeros(nterms, dtype=np.uint8)
    for i in range(nterms):
        jmin = max(0, i - nterms2 + 1)
        jmax = min(i, nterms1-1)
        for j in range(jmin, jmax+1):
            prod[i] ^= GF_mult(p1[j], p2[i-j])
    return prod
    


def GF_div_poly(p1, p2):
    # Compute the lengths of the given polynomials and the product 
    nterms1 = len(p1)
    nterms2 = len(p2)

    # If the dividend has fewer terms than the divisor, then the entire dividend is the remainder
    if nterms1 < nterms2:
        return p1
    
    nterms = nterms1 - nterms2
    ptmp = p1.copy()

    # Initialize an array to store the product
    for i in range(nterms+1):
        if ptmp[i] == 0:
            continue
        
        fact = GF_div(ptmp[i], p2[0])
        # print("Factor = ", fact)
        for j in range(nterms2):
            ptmp[i+j] ^= GF_mult(p2[j], fact)
        # print(ptmp)

    return ptmp[-nterms2+1:]


# Construct the polynomial for error correction of the data string 
def construct_ec_poly(nblocks):
    poly = [1,1]
    for i in range(1, nblocks):
        poly = GF_mult_poly(poly, [1,GF_antilogs[i]])
    return poly

# Compute the error correction bits for the array
def append_ecbits(arr, poly):
    nbits = len(arr)
    npoly = len(poly)

    tmparr = arr.copy()
    padded_poly = np.zeros(nbits, dtype=bool)
    padded_poly[:npoly] = poly

    start = find_start(tmparr)
    tmplen = nbits - start

    while tmplen > npoly:
        np.logical_xor(tmparr[start:], padded_poly[:tmplen], out=tmparr[start:])
        start = find_start(tmparr)
        tmplen = nbits - start

    start = nbits - npoly + 1 
    arr[start:] = tmparr[start:]



# Generate the log and antilog tables for the Galois field GF(2^8)
GF_logs, GF_antilogs = gen_GF_log_tables()