import numpy as np

from .utils import int_to_bool, binary_to_int
from .galois import construct_ec_poly, compute_ecbytes

# Maximum version number for the QR code
MAX_VERSION = 40

# Path to the file containing the data specifications for the QR code
DATASPEC_FILE = "qrgen/dataspec.txt"

# Maximum mumber of integer-valued elements in each line of the data specification file
LINE_LEN = 8


# Standard boolean strings to pad the data (as defined in the QR code specification)
PADDING = np.bool_([
    [1,1,1,0,1,1,0,0],    # 236 in binary
    [0,0,0,1,0,0,0,1]     # 17 in binary
    ])


class QRdata:

    """
    This class handles the encoding of the message to be stored in the QR code. It takes the message 
    string as input and generates a boolean string based on the encoding type (numeric, alphanumeric, 
    or binary) and the error correction level. The resulting boolean string can be placed directly 
    in the QR code.

    The details of the encoding format depend on the version and the error correction level.
    This information is looked up from a text file. In general, the data is split into blocks, 
    where each block consists of a number of message bytes and a number of error correction bytes.
    There could be up to two different types of blocks (depending on the version) with differing 
    numbers of message bytes (but the same number of error correction bytes). The error correction
    bytes are computed separately for each block. Finally ,the data string needs to be generated by
    interlacing various blocks. 
    """

    def __init__(self, version, dtype, errlvl):
        # Assuming that the input values have been sanitized by the QRcode class
        self.version = version
        self.dtype = dtype
        self.errlvl = errlvl

        self.dataspec = parse_dataspec(DATASPEC_FILE)


    # Function to generate the data string (including error correction bits) for the QR-code
    # This is the main function of the class that should be called after initialization 
    def encode(self, msg:str) -> None:
        self.msg = msg
        self.msglen = len(self.msg)

        if self.version == None:
            self.version = self.compute_version()
        
        # Calculate the allowed number of message bits and how it is to be split in blocks
        self.num_msgbytes, self.num_blocks, self.ecbytes_per_block, self.msgbytes_per_block = self.lookup_dataspec()

        # num_blocks() is a tuple with two elements, corresponding to the number of blocks of each type
        self.total_num_blocks = sum(self.num_blocks)
        self.num_databytes = self.num_msgbytes + self.total_num_blocks*self.ecbytes_per_block

        # In the following, the lengths in bytes are useful for computing the error-correction 
        # words, while the lengths in bits are useful for the boolean data string. To avoid 
        # multiple redundant multiplications by 8, we store both values separately.        
        self.num_msgbits = 8*self.num_msgbytes
        self.num_databits = 8*self.num_databytes

        # Calculate the number of bits to store the message length (header to the data)
        self.num_msglen_bits = self.compute_msglen_bits() 

        # Initialize an array to hold the raw encoded data (without error correction bits)
        self.rawdata = np.zeros(self.num_databits, dtype=bool)
        self.data = self.rawdata.copy()
        
        # Add the header which encodes the data type and message length
        self.header_len = self.add_header()
        
        # Convert the message string to a bitstring based on the data type
        # Returns the final index of the data array if successful and -1 otherwise
        ind = self.encode_msg()   
        self._pad_data(ind)
        
        # Split the data into blocks 
        self.msg_blocks, self.ec_blocks = self._split_data() 
        
        # These are identical for all blocks 
        ec_coeffs = construct_ec_poly(self.ecbytes_per_block)  
        
        # Compute the error correction bytes for each block
        for blocktype in range(2):       
            for i in range(self.num_blocks[blocktype]):
                msg_coeffs = self.msg_blocks[blocktype*self.num_blocks[0] + i, :self.msgbytes_per_block[blocktype]]
                self.ec_blocks[blocktype*self.num_blocks[0] + i] = compute_ecbytes(msg_coeffs, ec_coeffs)

        # Interlace the blocks to get the final data string
        data_bytelist = self._interlace_blocks() 

        # Convert the data_bytelist to a bitstring
        for i in range(self.num_databytes):
            self.data[8*i:8*(i+1)] = int_to_bool(data_bytelist[i], 8)



    # FUNCTIONS FOR LOOKING UP THE DATA ENCODING SPECIFICATIONS
    # =================================================================
        
    # Function to parse the data specification 
    def lookup_dataspec(self) -> tuple[int]:
        try:
            spec = self.dataspec[(self.version, self.errlvl)]
        except:
            raise ValueError(f"Data specification not found for version {self.version} and error correction level {self.errlvl}!")
        
        num_msgbytes = spec[0]
        ecbytes_per_block = spec[1]        
        num_blocks = (spec[2],spec[4])
        msgbytes_per_block = (spec[3],spec[5])

        return num_msgbytes, num_blocks, ecbytes_per_block, msgbytes_per_block


    # Function to compute the optimal version given the message length and error correction level
    def compute_version(self) -> int:
        for ver in range(1,MAX_VERSION):
            try:
                spec = self.dataspec[(ver, self.errlvl)]
            except:
                continue 
            if spec[0] >= self.msglen:
                return ver
        raise ValueError(f"Message too long for any version of the QR code with error correction level {self.errlvl}!")
        
    
    # Function to compute the number of bits for the data length
    # (based on the QR version and data type)
    def compute_msglen_bits(self) -> int:
        match self.dtype:
            case 0:     # Numeric encoding
                if self.version <= 9:
                    return 10
                elif self.version <= 26:
                    return 12   
                else:
                    return 14
            case 1:     # Alphanumeric encoding
                if self.version <= 9:
                    return 9    
                elif self.version <= 26:
                    return 11
                else:
                    return 13             
            case 2:     # Binary encoding
                if self.version <= 9:
                    return 8
                else:    
                    return 16
        


    # FUNCTIONS FOR STRUCTURING THE DATA FOR THE QR CODE 
    # =================================================================

    # Function to add the header to the data. 
    # The header consists of the data type followed by the message length        
    def add_header(self) -> int:
        # Encode the data type
        dtype_code = np.zeros(4, dtype=bool)
        dtype_code[-self.dtype-1] = True         
        self.rawdata[0:4] = dtype_code

        # Encode the message length
        header_len = self.num_msglen_bits + 4
        self.rawdata[4:header_len] = int_to_bool(self.msglen, self.num_msglen_bits)

        return header_len    


    # Function to pad the message. Note that since the array is initialized to False, 
    # padding with zeros is equivalent to simply moving the index
    def _pad_data(self, ind:int) -> None:    
        # If only up to four bits are left, then we are done
        if ind >= self.num_msgbits - 4:
            return 
        
        # Add the terminator string of 4 zeros
        ind += 4 

        # If the data length after this padding is not a multiple of 8, 
        # move ahead until it is. 
        rem = ind % 8
        if rem != 0: 
            ind += 8-rem

        # Alternatively pad with the two fixed boolean arrays stored in the constant PADDING
        # Pad with PADDING[0] if pflag is true and with PADDING[1] otherwise
        pflag = True
        while ind < self.num_msgbits:
            if pflag:
                self.rawdata[ind:ind+8] = PADDING[0]
            else:
                self.rawdata[ind:ind+8] = PADDING[1]
            pflag = not pflag 
            ind += 8

        return


    # Function to split the data into blocks (as required for version 3-40) 
    def _split_data(self) -> tuple[np.ndarray]: 
        # Maximum length of a block (in bytes)
        # When there are two distinct block types, then this is the length of the 
        # second type of block, which is one more than that for the first type
        msg_blocks = np.zeros((self.total_num_blocks, max(self.msgbytes_per_block)), dtype=int)
        ec_blocks = np.zeros((self.total_num_blocks, self.ecbytes_per_block), dtype=int)

        ind = 0 
        for blocktype in range(2):
            for i in range(self.num_blocks[blocktype]):
                for j in range(self.msgbytes_per_block[blocktype]):
                    # Convert 8-bit binary strings to integers
                    msg_blocks[blocktype*self.num_blocks[0] + i,j] = binary_to_int(self.rawdata[ind:ind+8])
                    ind += 8 

        return msg_blocks, ec_blocks


    # Function to interlace the blocks of data 
    def _interlace_blocks(self) -> np.ndarray: 
        ind = 0
        data_bytelist = np.zeros(self.num_databytes, dtype=int)

        if self.num_blocks[1] == 0:
            # If all message blocks have the same length, then read the blocks columnwise
            for i in range(max(self.msgbytes_per_block)):
                for j in range(self.total_num_blocks):
                    data_bytelist[ind] = self.msg_blocks[j,i]
                    ind += 1 
        else:
            # If the blocks have different lengths, then the (longer) second set of blocks 
            # must be treated differently 
            for i in range(max(self.msgbytes_per_block)-1):
                for j in range(self.total_num_blocks):
                    data_bytelist[ind] = self.msg_blocks[j,i]
                    ind += 1  
                    
            for j in range(self.num_blocks[1]):
                data_bytelist[ind] = self.msg_blocks[self.num_blocks[0] + j,-1]
                ind += 1  
                
        # The error correction blocks are all of the same length
        for i in range(self.ecbytes_per_block):
            for j in range(self.total_num_blocks):
                data_bytelist[ind] = self.ec_blocks[j,i]
                ind += 1 

        return data_bytelist



    # FUNCTIONS FOR ENCODING THE MESSAGE IN VARIOUS MODES
    # =================================================================
            
    # Set the remaining bits to a representation of the data based on the data type
    # This function returns the final index of the data array        
    def encode_msg(self) -> int:
        match self.dtype:
            case 0:
                ind = self._encode_numeric()
            case 1:
                # Need to convert to uppercase since alphanumeric encoding assumes only uppercase characters
                self.msg = self.msg.upper()
                ind = self._encode_alphanumeric()                
            case 2:
                ind = self._encode_binary()
                
        return ind 


    # Function to encode the message using the numeric mode 
    # Returns the final index of the data array
    # This encodes 3-digit blocks as a 10-bit string
    def _encode_numeric(self) -> int:
        # Need to double check this for the case where a block starts with 0!!!

        if not self.msg.isdecimal():
            raise ValueError("Cannot use numeric encoding, since the message contains non-numeric characters!")

        # Number of complete 3-digit blocks
        num_triplets = self.msglen // 3
        ind = self.header_len

        # Encode the message in blocks of 3 digits
        for i in range(num_triplets):
            self.rawdata[ind:ind+10] = int_to_bool(int(self.msg[3*i:3*i+3]), 10)
            ind += 10

        # Encode the remaining 1 or 2 digits
        if self.msglen % 3 == 1:
            self.rawdata[ind:ind+4] = int_to_bool(int(self.msg[-1]), 4)
            ind += 4
        elif self.msglen % 3 == 2:
            self.rawdata[ind:ind+7] = int_to_bool(int(self.msg[-2:]), 7)
            ind += 7

        return ind


    # Function to encode the message using the alphanumeric mode
    # Returns the final index of the data array
    # This encodes 2-character blocks as a 11-bit string
    def _encode_alphanumeric(self) -> int:
        # Compute the alphanumeric code corresponding to each character
        alphanum_list = np.zeros(self.msglen, dtype=int)
        for i in range(self.msglen):
            alphanum_list[i] = alphanum(self.msg[i])
        
        # Number of complete 2-character blocks
        num_pairs = self.msglen // 2
        ind = self.header_len        

        # Encode the pairs of characters 
        for i in range(num_pairs):
            self.rawdata[ind:ind+11] = int_to_bool(45*alphanum_list[2*i] + alphanum_list[2*i+1], 11)
            ind += 11
        
        # Encode the remaining character, if any
        if self.msglen % 2 == 1:
            self.rawdata[ind:ind+6] = int_to_bool(alphanum_list[-1], 6)
            ind += 6

        return ind


    # Function to encode the message using the binary mode
    def _encode_binary(self) -> int:
        ind = self.header_len
        for char in self.msg:
            self.rawdata[ind:ind+8] = int_to_bool(ord(char), 8)
            ind += 8

        return ind




# ADDITIONAL GLOBAL FUNCTIONS 
# =================================================================

# Function to convert a character to a number in the alphanumeric mode
def alphanum(char:chr) -> int:
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
            raise ValueError(f"The character {char} cannot be encoded in the alphanumeric mode!")
        

def parse_dataspec(filename:str) -> dict[tuple[int], list[int]]:
    """
    Parses the data specification stored in the file with the given filename.
    Returns a dictionary with the version and error correction level as keys and the corresponding
    data specification as values.

    The format of the data specification file is as follows:
        The first two integers in each line are the version and error correction level.
        The third integer denotes the maximum allowed number of message bytes. 
        The fourth integer is the number of error correction bytes per block.
        The next two integets are the number of blocks of type 1 and the number of message bytes per block.
        The next two integers are the corresponding quantities for blocks of type 2 (if applicable)
    """ 

    dataspec = {}
    with open(filename, "r") as file:
        for line in file:
            # Initialize an array to store the data specification
            strlist = line.strip().split('\t') 
            num_str = len(strlist)
            if num_str < 6:
                continue

            tmplist = np.zeros(LINE_LEN, dtype=int)        
            for i in range(num_str):
                tmplist[i] = int(strlist[i])

            version = tmplist[0]
            errlvl = tmplist[1]
            dataspec[(version,errlvl)] = tmplist[2:]
    return dataspec