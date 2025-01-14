import numpy as np 
from .QRmatrix import QRmatrix
from .general import int_to_bool, binary_to_int, int_to_binary, pad_alternating
from .encode import encode_numeric, encode_alphanumeric, encode_binary
from .galois import GF_div_poly, construct_ec_poly, append_ecbits


class QRcode:

    MAX_VERSION = 6

    FORMAT_MASK = np.bool_([1,0,1,0,1,0,0,0,0,0,1,0,0,1,0])
    FORMAT_POLYNOMIAL = np.bool_([1,0,1,0,0,1,1,0,1,1,1])
    VERSION_POLYNOMIAL = np.bool_([1,1,1,1,1,0,0,1,0,0,1,0,1])

    # Standard boolean strings to pad the data
    PADDING = np.bool_([[1,1,1,0,1,1,0,0],    # 236 in binary
                        [0,0,0,1,0,0,0,1]])     # 17 in binary
        

    DATATYPE_ID = {0:'Numeric', 1:'Alphanumeric', 2:'Binary'}
    

    EC_LEVEL_ID = {0:'M', 1:'L', 2:'H', 3:'Q'}
    EC_LEVEL_CODE = {'L':1, 'M':0, 'Q':3, 'H':2}
    

    # INITIALIZATION 
    # =================================================================
    def __init__(self, version, dtype, errcode):
        # Validate the input parameters
        # Maybe implement default cases here later
        if self.validate(version, dtype, errcode) < 0: 
            print("Invalid input. Aborting...")
            return 
        
        # Compute the size of the QR-code matrix
        self.size = 4*version + 17
        
        # Compute allowed number of message bits that can be encoded (excluding error correction). 
        # This depends on the version and the error correction level 
        self.num_msgbytes = self.compute_num_msgbytes() 
        self.num_msgbits = 8 * self.num_msgbytes
        
        # Initialize a QRmatrix object 
        self.qr = QRmatrix(self.version)

        # Add the version info block if required 
        if self.version >= 7:        
            ver_arr = np.zeros(3*(self.CORNER_SIZE-1), dtype=bool)   
            ver_arr[:self.CORNER_SIZE-1] = int_to_bool(self.version,self.CORNER_SIZE-1) 

            # The version info is encoded with the version polynomial
            append_ecbits(ver_arr, self.VERSION_POLYNOMIAL)

            # Add to the QR code matrix 
            self.qr.add_version_info(ver_arr)

        # Initialize the number of data modules (bits) to the total number of modules
        self.num_databits = self.size ** 2 - self.qr.num_func_bits   

        # Make the number of allowed data modules a multiple of 8
        self.num_databytes = self.num_databits // 8
        self.num_rembits = self.num_databits - 8 * self.num_databytes
        self.num_databits = 8 * self.num_databytes

        # Initialize a boolean array to hold the data to be encoded 
        self.data_arr = np.zeros(self.num_databits, dtype=bool)

        return 



    def validate(self, version, dtype, errcode):
        if type(version) != int:
            print("The version must be an integer.")
            return -1 
        
        if version < 1 or version > 41: 
            print("The version must be an integer between 1 and 41.")
            return -1 
        
        if version > self.MAX_VERSION: 
            print("Only versions up to ", self.MAX_VERSION, " are currently supported. :( ")
            return -1 
            
        if type(dtype) != int:
            print("The data type must be an integer.")
            return -1 
        
        if dtype < 0 or dtype > 3:
            print("The data type must be an integer between 0 and 3 (inclusive).")
            return -1 
            
        if type(errcode) == int:
            if 0 <= errcode <= 3:
                self.ec_level = errcode
            else:                
                print("Valid error correction levels are between 0 and 3")
                return -1
                        
        elif type(errcode) == str:
            if errcode in ['L','M', 'Q','H']:
                self.ec_level = self.EC_LEVEL_CODE[errcode]
            else:                
                print("Valid error correction levels are L, M, Q, and H.")
                return -1
        else:                
            print("The error correction level must be an integer or a single character.")
            return -1 
        
        self.version = version
        self.datatype = dtype

        return 1 


    # PRINTING ROUNTINES
    # =================================================================

    def __str__(self):
        return self.msg
    
    
    # Function to display the QR-code as an image 
    def display(self):
        from PIL import Image
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(1, 1, figsize=(14, 6))
        ax.axis('off')
        fig.subplots_adjust(left=0.25, right=0.75, top=0.75, bottom=0.25)
        qr_image = Image.fromarray(np.uint8(~self.qr.mat) * 255)

        # Pad the image with whitespace
        padding = 6
        padded_image = Image.new('L', (qr_image.size[0] + 2 * padding, qr_image.size[1] + 2 * padding), 255)
        padded_image.paste(qr_image, (padding, padding))

        ax.imshow(padded_image, cmap='gray', vmin=0, vmax=255)
        plt.show()


    # Function to print various stats about the QR code
    def print_stats(self): 
        print("QR Code:")
        print("  Version =", self.version)
        print("  Data format =", self.DATATYPE_ID[self.datatype])
        print("  Error Correction Level =", self.EC_LEVEL_ID[self.ec_level])
        print("  String encoded =", self.msg)
        print() 
        print("  QR code size =", self.size, "x", self.size, "modules")
        print("  Data length =", self.num_databits, "modules =", self.num_databytes, "words")
        print("  Allowed message length =", self.num_msgbits, " modules =", self.num_msgbytes, "words")
        print("  Number of error correction words =", self.num_databytes - self.num_msgbytes)
        print("  Remainder = ", self.num_rembits, "modules")
        print()
        print("  Encoded using pattern mask number", self.masknum)

    

    # COMPUTATIONS OF ALLOWED SIZES OF VARIOUS BITSTRINGS
    # =================================================================

    # Function to compute the number of message blocks
    # (based on the QR version and error correction level)
    def compute_num_msgbytes(self): 
        mat = np.array([
            [16,19,9,13],
            [28,34,16,22],
            [44,55,26,34],
            [64,80,36,48],
            [86,108,46,62],
            [108,136,60,76]
            ])
        return mat[self.version-1, self.ec_level]


    # Function to compute the number of modules(bits) used to represent the message length
    def compute_msglen_num_mods(self):
        if self.version <= 9:
            var = 0
        elif self.version <= 26:
            var = 1
        else:    
            var = 2

        if self.datatype == 0:
            nbits = 10 + 2*var
        elif self.datatype == 1:
            nbits = 9 + 2*var
        elif self.datatype == 2:
            nbits = 8 + 4*var
        elif self.datatype == 3:
            nbits = 8 + 2*var

        return nbits
    


    # DATA ENCODING
    # =================================================================

    # Function to initialize an array to store the data and set the header
    def init_data_arr(self, msg_str): 
        self.msg = msg_str

        msglen_size = self.compute_msglen_num_mods()
        header_size = msglen_size + 4

        # The first four bits are the data type
        datatype_code = np.zeros(4, dtype=bool)
        datatype_code[-self.datatype-1] = True         
        self.data_arr[0:4] = datatype_code

        # The next msg_len bits encode the length of the message
        msglen = len(self.msg)
        self.data_arr[4:header_size] = int_to_bool(msglen, msglen_size)

        # Set the remaining bits to a representation of the data based on the data type
        # This function returns the final index of the data array
        match self.datatype:
            case 0:
                ind = encode_numeric(self.data_arr, self.msg, header_size)
            case 1:
                self.msg = self.msg.upper()
                ind = encode_alphanumeric(self.data_arr, self.msg, header_size)
                # Need upper() since alphanumeric encoding assumes only uppercase characters
            case 2:
                ind = encode_binary(self.data_arr, self.msg, header_size)
            case _:
                ind = -1 
        
        return ind 
    

    # Function to add the error correction bits to the data array
    def append_data_ecbits(self):
        # Construct the data polynomial from the data array
        data_poly = np.zeros(self.num_databytes, dtype=np.uint8)
        for i in range(self.num_databytes):
            data_poly[i] = binary_to_int(self.data_arr[8*i:8*(i+1)])
        
        # Construct the generating polynomial for error correction 
        # The order of this polynomial is equal to the number of error correction blocks 
        num_ecblocks = self.num_databytes - self.num_msgbytes
        ec_poly = construct_ec_poly(num_ecblocks)  
                
        # Compute the remainder of the polynomial division in GF(2^8)
        rem_poly = GF_div_poly(data_poly, ec_poly)
        
        ind = self.num_msgbits
        for i in range(num_ecblocks):
            self.data_arr[ind:ind+8] = int_to_binary(rem_poly[i], 8)
            ind += 8

        return 
    

    # Function to encode the given message into the variable self.data_arr
    def encode(self, msg_str):     
        # Initialize the data array with the header and the message
        ind = self.init_data_arr(msg_str)
        
        # Pad to msg_bits (using the sequence specified in the QR code standard)
        pad_alternating(self.data_arr, ind, self.num_msgbits, self.PADDING)

        # Add error correction bits 
        self.append_data_ecbits()
        
        # Add to the QR code matrix 
        self.qr.add_data(self.data_arr)
        self.pattern_mask()

        return 


    # Function to generate the format string for a given error level and mask number
    def gen_format_arr(self, masknum):
        # Initialize the format string
        fmt = np.zeros(2*self.qr.CORNER_SIZE+1, dtype=bool)   

        # The first two bits are the error correction level
        fmt[0:2] = int_to_bool(self.ec_level,2) 
        
        # The next three bits are the mask pattern number      
        fmt[2:5] = int_to_bool(masknum,3)

        # Add the error correction bits to the format string
        append_ecbits(fmt, self.FORMAT_POLYNOMIAL)
        np.logical_xor(fmt, self.FORMAT_MASK, out=fmt)

        return fmt 


    def pattern_mask(self):
        # Initialize the max_penalty to something large
        max_penalty = 100000
        best_mask_num = -1
        best_qrmat = self.qr.mat.copy()

        # from PIL import Image
        # import matplotlib.pyplot as plt
        # fig, ax = plt.subplots(1, 8, figsize=(40, 5))

        # Iterate over all possible mask patterns 
        for masknum in range(0, 8):
            # Add the format information array for the current mask number
            fmt_arr = self.gen_format_arr(masknum)
            self.qr.add_format_info(fmt_arr)

            # Copy the current QR code matrix
            cur_qrmat = self.qr.mat.copy()

            # Apply the pattern mask to the current QR code matrix
            combined_mask = np.logical_and(self.qr.fmask, self.qr.pmasks[masknum])
            np.logical_xor(cur_qrmat, combined_mask, out=cur_qrmat)            

            # cur_image = Image.fromarray(np.uint8(~cur_qrmat) * 255)
            # ax[masknum].imshow(cur_image, cmap='gray', vmin=0, vmax=255)
            # ax[masknum].axis('off')

            # Score the current QR code matrix
            penalty = eval_qrmat(cur_qrmat, self.size)

            # Update the best QR matrix and score if the current score is better
            if penalty < max_penalty:
                max_penalty = penalty
                best_mask_num = masknum
                best_qrmat = cur_qrmat

        # Set the QR code matrix to the best one found
        self.masknum = best_mask_num
        self.qr.mat = best_qrmat

        return best_qrmat
            
        
def eval_qrmat(mat, len):
    # Penalty factors (as per the QR code standard)
    RUN_FACTOR = 3 
    BLOCK_FACTOR = 3
    CORNER_FACTOR = 40
    HOM_FACTOR = 10
    
    penalty = 0 
    hrun = 0 
    vrun = 0 
    
    # Check for runs of dark/light modules
    for i in range(0, len):
        hrun = 0 
        vrun = 0 
        for j in range(1, len):
            # Check for horizontal runs
            if mat[i,j] == mat[i,j-1]:
                hrun += 1
            else:
                if hrun >= 5:
                    penalty += RUN_FACTOR + hrun - 5
                hrun = 0

            # Check for vertical runs 
            if mat[j,i] == mat[j-1,i]:
                vrun += 1
            else:
                if vrun >= 5:
                    penalty += RUN_FACTOR + vrun - 5
                vrun = 0

    # Check for 2x2 blocks of dark/light modules
    for i in range(1, len):
        for j in range(1, len):
            # Check for horizontal blocks
            if mat[i,j] == mat[i-1,j-1] == mat[i-1,j] == mat[i,j-1]:
                penalty += BLOCK_FACTOR

    # Check for deviation from a 50-50 distribution of dark modules
    darkmod_count = np.sum(mat)
    darkmod_frac = darkmod_count / (len*len)
    penalty += np.uint8(np.floor(abs(darkmod_frac - 0.5))) * HOM_FACTOR 
    
    return penalty
