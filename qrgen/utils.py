import numpy as np

"""
This module contains general utility functions used in the QR code encoding and decoding process.
"""


# This function returrns a boolean array of length ndigits, with the binary representation of n.
# If n consists of more than ndigits bits, then the most significant bits are ignored.
def int_to_bool(n, ndigits) -> list[bool]:
    # Initialize the boolean array
    binarr = [False] * ndigits
    # binarr = np.zeros(ndigits, dtype=bool)

    # String representation of the binary number
    binstr = bin(n)[2:]
    imax = min(ndigits, len(binstr))

    for i in range(1, imax + 1):
        if binstr[-i] == "1":
            binarr[-i] = True

    return binarr


# Function to convert a uint8 array of 0's and 1's to a positive integer
def binary_to_int(bin_arr):
    num = 0
    for i in range(len(bin_arr)):
        num *= 2
        num += bin_arr[i]
    return num


# Function to convert a positive integer to an array of 0's and 1's of length len
def int_to_binary(num, nbits):
    bin_arr = np.zeros(nbits, dtype=np.uint8)
    for i in range(nbits):
        bin_arr[-i - 1] = num % 2
        num = num // 2
    return bin_arr


# Function to check if a string contains non-numeric characters
def contains_non_numeric(datastr):
    for char in datastr:
        if not char.isdigit():
            return True
    return False
