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


# 
def pad_alternating(arr, dlen, maxlen, padding):
    if maxlen - dlen <= 4:
        # Nothing to do here, since the array is initialized to False
        return 
    
    start = dlen + 4 
    rem = start % 8

    # If the data length after this padding is not a multiple of 8, 
    # move ahead until it is. 
    if rem != 0: 
        start += 8-rem

    # print("Padding from ", dlen, " to ", maxlen, " starting at ", start)

    while start < maxlen:
        # Alternatively pad with the two fixed strings
        arr[start:start+8] = padding[(start % 16) // 8]
        start += 8
