import numpy as np 
from .general import find_start

FORMAT_MASK = np.bool_([1,0,1,0,1,0,0,0,0,0,1,0,0,1,0])
FORMAT_POLYNOMIAL = np.bool_([1,0,1,0,0,1,1,0,1,1,1])
VERSION_POLYNOMIAL = np.bool_([1,1,1,1,1,0,0,1,0,0,1,0,1])


# Function to convert a uint8 array of 0's and 1's to a positive integer
def binary_to_int(bin_arr):
    num = 0 
    for i in range(len(bin_arr)):
        num *= 2 
        num += bin_arr[i]
    return num


# Function to convert a positive integer to an array of 0's and 1's of length len
def int_to_binary(num,nbits):
    bin_arr = np.zeros(nbits,dtype=np.uint8)
    for i in range(nbits):
        bin_arr[-i-1] = num % 2
        num = num // 2
    return bin_arr

GALOIS_GEN = np.bool_([1,0,0,0,1,1,1,0,1])   # 285 in binary 

# Function to compute 2x for a given x in the Galois field GF(2^8) with a given generator polynomial
def galois_double(arr, gen_poly):
    nbits = len(gen_poly)
    tmp = np.zeros(nbits, dtype=bool)
    tmp[:8] = arr
    if tmp[0]:
        return np.logical_xor(tmp, gen_poly)[1:]
    else:    
        return tmp[1:]
    

# Function to generate the log and antilog tables for the Galois field GF(2^8)
def gen_GF_log_tables():
    # Start with the seed 1 (defined as a boolean array of length 8)
    seed = np.zeros(8, dtype=bool)
    seed[-1] = True

    # Initialize a dictionary to store the antilogs as n:2^n for n in 0,1,...,254
    GF_antilogs = {}
    for i in range(255):
        GF_antilogs[i] = binary_to_int(seed)
        seed = galois_double(seed, GALOIS_GEN)

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



def compute_num_ecblocks(version, dtype, errlvl): 
    # Need to implement this 
    return 10




def append_data_ecbits(data, dtype, errlvl, version, ind):

    # Compute the number of error correction blocks 
    nblocks = compute_num_ecblocks(version, dtype, errlvl)

    # Compute the generating polynomial for the error correction bits
    ec_poly = construct_ec_poly(nblocks)
    
    # Encode the message 
    intlen = len(data) // 8 
    data_poly = np.zeros(intlen, dtype=np.uint8)
    for i in range(intlen):
        data_poly[i] = binary_to_int(data[8*i:8*(i+1)])
    
    # Compute the remainder of the polynomial division in GF(2^8)
    rem = GF_div_poly(data_poly, ec_poly)
    
    # print("EC Poly = ")
    # print(ec_poly)
    # print("Data Poly = ")
    # print(data_poly)
    # print()
    # print("ECC blocks = ")
    # print(rem)
    # print()
    
    for i in range(nblocks):
        data[ind:ind+8] = int_to_binary(rem[i], 8)
        ind += 8

    return 0


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



def append_format_ecbits(arr): 
    append_ecbits(arr, FORMAT_POLYNOMIAL)
    np.logical_xor(arr, FORMAT_MASK, out=arr)
    return 


def append_version_ecbits(arr): 
    append_ecbits(arr, VERSION_POLYNOMIAL)


# Generate the log and antilog tables for the Galois field GF(2^8)
GF_logs, GF_antilogs = gen_GF_log_tables()