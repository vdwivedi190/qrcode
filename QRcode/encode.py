import numpy as np 
from .general import int_to_bool
from .errcorrection import append_data_ecbits
from .populate import add_data

# Standard boolean strings to pad the data
PADDING = np.bool_([
    [1,1,1,0,1,1,0,0],    # 236 in binary
    [0,0,0,1,0,0,0,1]     # 17 in binary
    ])

# Function to compute the code corresponding to the data type
def gen_dtypestr(dtype):
    dcode = np.zeros(4, dtype=bool)
    dcode[-dtype-1] = True 
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
    return 128

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

    while start < maxlen:
        # Alternatively pad with the two fixed strings
        arr[start:start+8] = PADDING[(start % 16) // 8]
        start += 8


def alphanum(char):
    match char:
        case _ if '0' <= char <= '9':  # Digits 0-9
            return ord(char) - 48
        case _ if 'A' <= char <= 'Z':  # (Uppercase) letters A-Z
            return ord(char) - 55
        case ' ':
            return 36
        case '$':
            return '37'
        case '%':
            return 38
        case '*':
            return 39
        case "+":
            return 40
        case "-":
            return 41
        case ".":
            return 42
        case "/":
            return 43
        case ":":
            return 44
        case _:
            print("The character", char, "cannot be encoded in the alphanumeric mode!")
            return -1

# def alphanum(char):
#     num = ord(char)
#     match num:
#         case _ if 48 <= num <= 57:  # Digits 0-9
#             return num - 48
#         case _ if 65 <= num <= 90:  # (Uppercase) letters A-Z
#             return num - 55
#         case 32:
#             return 36
#         case 36:
#             return 37
#         case 37:
#             return 38
#         case 43:
#             return 39
#         case 45:
#             return 40
#         case _:
#             print("The character", char, "cannot be encoded in the alphanumeric mode!")
#             return -1


def alphanum_encode(data_arr, datastr, ind):
    nblocks = len(datastr) // 2 # Number of 2-character blocks

    for i in range(nblocks):
        # Compute the number corresponding to character 
        num1 = alphanum(datastr[2*i])
        num2 = alphanum(datastr[2*i+1])
        if num1 == -1 or num2 == -1:  # Invalid character
            return -1
        data_arr[ind:ind+11] = int_to_bool(45*num1 + num2, 11)
        ind += 11
    
    if len(datastr) % 2 == 1:
        num1 = alphanum(datastr[-1])
        if num1 == -1:  # Invalid character
            return -1
        data_arr[ind:ind+6] = int_to_bool(alphanum(datastr[-1]), 6)
        ind += 6
    
    return ind



def gen_datastr(data_arr, datastr, dtype, ind):
    if dtype == 0:  # Numeric data
        # Need to double check this for the case where a block starts with 0
        nblocks = len(datastr) // 3  # Number of 3-digit blocks
        for i in range(nblocks):
            data_arr[ind:ind+10] = int_to_bool(int(datastr[3*i:3*i+3]), 10)
            ind += 10
        if len(datastr) % 3 == 1:
            data_arr[ind:ind+4] = int_to_bool(int(datastr[-1]), 4)
            ind += 4
        elif len(datastr) % 3 == 2:
            data_arr[ind:ind+7] = int_to_bool(int(datastr[-2:]), 7)
            ind += 7

    elif dtype == 1:  # Alphanumeric data
        datastr = datastr.upper()
        ind = alphanum_encode(data_arr, datastr, ind)
        if ind == -1:
            return -1

    elif dtype == 2:  # Byte data
        for char in datastr:
            data_arr[ind:ind+8] = int_to_bool(ord(char), 8)
            ind += 8

    return ind-1


def encode_data(qrmat, fmask, data, dtype, version, errlvl, max_bits): 
    # Length of the message. This might be more complicated
    datalen = len(data)
    data_arr = np.zeros(max_bits, dtype=bool) 

    # Compute the number of data bits that can be encoded
    data_bits = compute_max_datalen(version, errlvl)

    dcode_bits = 4 
    datalen_bits = compute_lenbits(version, dtype)
    head_bits = dcode_bits + datalen_bits 

    # datalen_code = int_to_bool(datalen, datalen_bits)

    # Set the first four bits to data type 
    data_arr[0:dcode_bits] = gen_dtypestr(dtype)

    # Set the next 8 bits to the length of the text message
    data_arr[dcode_bits:head_bits] = int_to_bool(datalen, datalen_bits)

    # Set the remaining bits to a representation of the data based on the data type
    # This function returns the final index of the data array
    ind = gen_datastr(data_arr, data, dtype, head_bits) 

    # print("Index = ", ind, ", padding to ", data_bits)
    if ind < 0:
        return 
    
    # Pad to msg_bits 
    pad_arr(data_arr, ind, data_bits)

    # Add error correction bits 
    append_data_ecbits(data_arr, dtype, errlvl, version, data_bits)

    # print(np.uint8(data_arr))

    # Add to the QR code matrix 
    add_data(qrmat, version, fmask, data_arr)

    return data_arr

