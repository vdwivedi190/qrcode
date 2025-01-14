import numpy as np 
from .general import find_start, binary_to_int, int_to_binary
from .galois import GF_mult_poly, GF_div_poly, GF_logs, GF_antilogs

FORMAT_MASK = np.bool_([1,0,1,0,1,0,0,0,0,0,1,0,0,1,0])
FORMAT_POLYNOMIAL = np.bool_([1,0,1,0,0,1,1,0,1,1,1])
VERSION_POLYNOMIAL = np.bool_([1,1,1,1,1,0,0,1,0,0,1,0,1])

GALOIS_GEN = np.bool_([1,0,0,0,1,1,1,0,1])   # 285 in binary 


# Construct the polynomial for error correction of the data string 
def construct_ec_poly(nblocks):
    poly = [1,1]
    for i in range(1, nblocks):
        poly = GF_mult_poly(poly, [1,GF_antilogs[i]])
    return poly


def compute_num_ecblocks(version, dtype, errlvl): 
    # Need to implement this 
    return 10


def append_data_ecbits(data, dtype, errlvl, version, ind, nblocks):
    # Compute the number of error correction blocks 
    # nblocks = compute_num_ecblocks(version, dtype, errlvl)
    print("Number of error correction blocks = ", nblocks)

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
# GF_logs, GF_antilogs = gen_GF_log_tables()