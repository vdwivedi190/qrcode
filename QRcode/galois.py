import numpy as np 

"""
This modules contains functions to perform arithmetic operations in the Galois field
GF(2) and GF(2^8). These operations are used in the Reed-Solomon error correction 
algorithm in the QR code standard. 

"""
# Generator for the Galois field GF(2^8). The bits in the binary representation of 285 
# are interpreted as the coefficients of the polynomial over GF(2)
GALOIS_GEN = 285   



# GENERATING THE LOG AND ANTILOG TABLES
# =============================================

# Function to generate the log and antilog tables for the Galois field GF(2^8)
def gen_GF_log_tables():
    # Initialize a dictionary to store the antilogs as n:2^n for n in 0,1,...,254
    GF_antilogs = {}
    
    num = 1
    GF_antilogs[0] = num

    for i in range(1,255):
        num *= 2
        if num > 255:
            # Bitwise XOR with the generator polynomial
            # This ensures that num remains in the Galois field
            num ^= GALOIS_GEN  
        GF_antilogs[i] = num

    # Invert the dictionary to get the logs 
    GF_logs = {val: key for key, val in GF_antilogs.items()}

    return GF_logs, GF_antilogs

# Generate the log and antilog tables for the Galois field GF(2^8)
GF_logs, GF_antilogs = gen_GF_log_tables()



# ARITHEMETIC OPERATIONS IN GF(2^8)
# =============================================

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
    


# Division of two polynomials in the Galois field GF(2^8) using precomputed log tables
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




# COMPUTING THE ERROR CORRECTION BITS
# =============================================

# Construct the polynomial for error correction of the data string 
def construct_ec_poly(nblocks):
    poly = [1,1]
    for i in range(1, nblocks):
        poly = GF_mult_poly(poly, [1,GF_antilogs[i]])
    return poly


# function to find first True in a boolean array
def find_start(arr):
    for i in range(len(arr)):
        if arr[i]:
            return i
    return len(arr)


# Compute the error correction bits for a boolean array
def compute_ecbits(msg_coeffs, ec_coeffs):
    msg_len = len(msg_coeffs)
    ec_len = len(ec_coeffs)
    total_len = msg_len + ec_len - 1

    tmp_coeffs = np.zeros(total_len, dtype=bool)
    tmp_coeffs[:msg_len] = msg_coeffs

    start = find_start(tmp_coeffs)
    while start + ec_len <= total_len:
        np.logical_xor(tmp_coeffs[start:start+ec_len], ec_coeffs, out=tmp_coeffs[start:start+ec_len])
        start = find_start(tmp_coeffs)

    return tmp_coeffs[-ec_len+1:]


# Compute the error correction bytes for an integer array
# (equivalent to an array with elements in GF(2^8))
def compute_ecbytes(msg_coeffs, ec_coeffs):
    msg_len = len(msg_coeffs)
    ec_len = len(ec_coeffs)
    tmp_coeffs = np.zeros(msg_len + ec_len - 1, dtype=int)
    tmp_coeffs[:msg_len] = msg_coeffs
    return GF_div_poly(tmp_coeffs, ec_coeffs)[-len(ec_coeffs):]

