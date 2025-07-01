import numpy as np

"""
This module contains general utility functions used in the QR code encoding and decoding process.
"""


def str_to_bool_list(bool_str: str, str_len: int | None = None) -> list[bool]:
    """Convert a boolean string to a boolean array of length ndigits, representing its binary form.

    Args:
        n (int): The positive integer to convert.
        ndigits (int): The length of the resulting boolean array.

    Returns:
        list[bool]: A boolean array of length ndigits, where True represents 1 and False represents 0.
    """
    if str_len is None:
        str_len = len(bool_str)

    if len(bool_str) > str_len:
        raise ValueError(
            f" cannot encode a string of length {len(bool_str)} in {str_len} bits"
        )

    if any(c not in "01" for c in bool_str):
        raise ValueError(
            f"Invalid boolean string '{bool_str}'. Only '0' and '1' are allowed."
        )

    pad_len = str_len - len(bool_str)
    return [False] * pad_len + [c == "1" for c in bool_str]


def int_to_bool_list(num: int, ndigits: int) -> list[bool]:
    """Convert a positive integer to a boolean array of length ndigits, representing its binary form.

    Args:
        n (int): The positive integer to convert.
        ndigits (int): The length of the resulting boolean array.

    Returns:
        list[bool]: A boolean array of length ndigits, where True represents 1 and False represents 0.
    """

    return str_to_bool_list(bin(num)[2:], ndigits)


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
