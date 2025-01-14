import numpy as np 
from .general import int_to_bool

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


# Function to compute the maximum number of data modules for a given
# version and level of error correction
def compute_max_datalen(version, errlvl): 
    # Need to write this function! 
    mat = 8*np.array([
        [16,19,9,13],
        [28,34,16,22],
        [44,55,26,34],
        [64,80,36,48],
        [86,108,46,62],
        [108,136,60,76]
        ])
    return mat[version-1,errlvl]


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
    print("Length of data array = ", len(arr))
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


def encode_numeric(data_arr, datastr, ind):
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

    return ind


def encode_alphanumeric(data_arr, datastr, ind):
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


def encode_binary(data_arr, datastr, ind):
    for char in datastr:
        data_arr[ind:ind+8] = int_to_bool(ord(char), 8)
        ind += 8

    return ind

