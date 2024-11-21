import numpy as np 

# This function returrns a boolean array of length ndigits, with the binary representation of n.
# If n consists of more than ndigits bits, then the most significant bits are ignored.
def int_to_bool(n, ndigits):
    # Initialize the boolean array 
    binarr = np.zeros(ndigits, dtype=bool)

    # String representation of the binary number
    binstr = bin(n)[2:]
    imax = min(ndigits, len(binstr))
    
    for i in range(1,imax+1):
        if binstr[-i] == '1':
            binarr[-i] = True

    return binarr


# function to find first True in a boolean array
def find_start(arr):
    for i in range(len(arr)):
        if arr[i]:
            return i
    return len(arr)

