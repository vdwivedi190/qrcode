import numpy as np 
from .general import int_to_bool
from .errcorrection import append_data_ecbits
from .populate import add_data

# Standard boolean strings to pad the data
PADDING = np.bool_([[1,1,1,0,1,1,0,0],
                    [0,0,0,1,0,0,0,1]])

# Function to compute the code corresponding to the data type
def gen_dtypestr(dtype):
    dcode = np.zeros(4, dtype=bool)
    dcode[dtype] = True 
    return dcode


# This function encodes a text message and header into a boolean array and returns the final position.
# The header consists of 4 bits for the data type and 8 bits for the length of the text message. 
def msg_encode(msg_arr, text, dtype):
    txt_len = len(text)

    dcode_len = 4
    
    dtype_code = compute_dtype(dtype)
    sz_len = compute_szbits(dtype)
    head_len = dcode_len + sz_len 

    # Set the first four bits to data type 
    msg_arr[0:dcode_len] = dtype_code 

    # Set the next 8 bits to the length of the text message
    msg_arr[dcode_len:head_len] = int_to_bool(txt_len, 8)

    # Set the remaining bits to the ASCII representation of the text message
    for i in range(txt_len):
        msg_arr[(head_len+8*i):(head_len+8*(i+1))] = int_to_bool(ord(text[i]), 8)

    return head_len+8*txt_len-1 



# Function to compute the maximum number of data modules for a given
# version and level of error correction
def compute_max_datalen(version, errlvl): 
    # Need to write this function! 
    return 16*version**2


# Function to compute the number of bits for the data length
# (based on the QR version and data type)
def compute_lenbits(version, dtype):
    if version <= 9:
        var = 0
    elif version <= 26:
        var = 1
    else:    
        var = 2

    if dtype == 0:
        return 10 + 2*var
    elif dtype == 1:
        return 9 + 2*var
    elif dtype == 2:
        return 8 + 4*var
    elif dtype == 3:
        return 8 + 2*var
    


def pad_arr(arr, dlen, maxlen):
    if maxlen - dlen <= 4:
        # Nothing to do here, since the array is initialized to False
        return 
    
    start = dlen + 4 
    rem = start % 8

    # If the data length after this padding is not a multiple of 8, 
    # move ahead until it is. 
    if rem != 0: 
        start += 8-rem

    while start <= maxlen:
        # Alternatively pad with the two fixed strings
        arr[start:start+8] = PADDING[(start % 16) // 8]
        start += 8



def encode_data(qrmat, fmask, data, dtype, version, errlvl, max_bits): 
    # Length of the message. This might be more complicated
    datalen = len(data)
    data_arr = np.zeros(max_bits, dtype=bool) 

    # Compute the number of data bits that can be encoded
    data_bits = compute_max_datalen(version, errlvl)

    dcode_bits = 4 
    datalen_bits = compute_lenbits(version, dtype)
    head_bits = dcode_bits + datalen_bits 

    # dtype_code = gen_dtypestr(dtype)
    # datalen_code = int_to_bool(datalen, datalen_bits)

    # Set the first four bits to data type 
    data_arr[0:dcode_bits] = gen_dtypestr(dtype)

    # Set the next 8 bits to the length of the text message
    data_arr[dcode_bits:head_bits] = int_to_bool(datalen, datalen_bits)

    # Set the remaining bits to the ASCII representation of the text message
    for i in range(datalen):
        data_arr[(head_bits+8*i):(head_bits+8*(i+1))] = int_to_bool(ord(data[i]), 8)

    # Pad to msg_bits 
    pad_arr(data_arr, head_bits + 8*datalen, data_bits)

    # Add error correction bits 
    append_data_ecbits(data_arr, errlvl)

    # Add to the QR code matrix 
    add_data(qrmat, version, fmask, data_arr)

