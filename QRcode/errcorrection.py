import numpy as np 
from .general import find_start

FORMAT_MASK = np.bool_([1,0,1,0,1,0,0,0,0,0,1,0,0,1,0])
FORMAT_POLYNOMIAL = np.bool_([1,0,1,0,0,1,1,0,1,1,1])
VERSION_POLYNOMIAL = np.bool_([1,1,1,1,1,0,0,1,0,0,1,0,1])

def append_data_ecbits(data, errlvl):
    return 0


# Compute the error correction bits for the array
def append_ecbits(arr, poly):
    nbits = len(arr)
    npoly = len(poly)

    tmparr = np.copy(arr)
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
