import numpy as np 
from PIL import Image
import matplotlib.pyplot as plt

from .QRmatrix import QRmatrix
from .QRdata import QRdata, DATASPEC_FILE
# from .general import int_to_bool, binary_to_int, int_to_binary, pad_alternating
# from .galois import GF_div_poly, construct_ec_poly, append_ecbits


class QRcode:
    MAX_VERSION = 40
        
    DATATYPE_ID = {0:'Numeric', 1:'Alphanumeric', 2:'Binary'}    
    MAX_CAPACITY = {0:7089, 1:4296, 2:2953}

    EC_LEVEL_ID = {0:'M', 1:'L', 2:'H', 3:'Q'}
    EC_LEVEL_CODE = {'L':1, 'M':0, 'Q':3, 'H':2}
    

    # INITIALIZATION 
    # Default encoding = binary 
    # Default error correction level = M
    # If a version number is not provided, then it is computed based on the length of the message
    def __init__(self, msg, version=0, dtype=2, errcode='M'):
        # Check if the QR code has been generated (Useful for the display/export functions)
        self.gen_flag = False 

        self.msg = msg
        self.msglen = len(msg)

        if type(version) == int and 0 <= version <= self.MAX_VERSION:
            self.version = version 
        else:
            print("Invalid version number. Aborting...")
            return

        if type(dtype) == int and 0 <= dtype <= 3:
            self.dtype = dtype  
        else:
            print("Invalid data type. Aborting...")
            return
        
        if type(errcode) == str and errcode in ['L','M','Q','H']:
            self.errlvl = self.EC_LEVEL_CODE[errcode]
        else:
            print("Invalid error correction level. Aborting...")
            return

        if self.msglen > self.MAX_CAPACITY[self.dtype]:
            print("Message too long for the given data type. Aborting...")
            return

        if self.version == 0:
            self.version = self.lookup_datasize() 
    
        self.data_obj = QRdata(self.version, self.dtype, self.errlvl)

        # Check if the message is too long for the given version
        if self.data_obj.num_msgbytes < self.msglen:
            print("Message too long for the given version. Aborting...")
            return
        
        self.data_obj.encode(self.msg)
        self.data = self.data_obj.data

        # Initialize a QRmatrix object 
        self.qr_obj = QRmatrix(self.version, self.errlvl)

        # Add to the QR code matrix 
        self.qr_obj.add_data(self.data_obj.data)
        self.qr_obj.pattern_mask()
        self.gen_flag = True 

        return 


    def lookup_datasize(self):
        optimal_version = -1

        # Start from the first line of the file with the desired error correction level
        starting_line = self.errlvl
        for j in range(1,starting_line):
            next(file)  

        with open(DATASPEC_FILE, "r") as file:
            for i in range(1,self.MAX_VERSION,4):
                line = file.readline()
                strlist = line.strip().split('\t') 
                if int(strlist[2]) >= self.msglen:
                    optimal_version = int(strlist[0])
                    break

                # Skip 4 lines to arrive at the next version with the same error correction level
                for j in range(1,4):
                    next(file)  

        return optimal_version


    # PRINTING ROUNTINES
    # =================================================================

    def __str__(self):
        if not self.gen_flag:
            return "QR code not generated!"
        return "Encoded message = " + self.msg
    
    
    # Function to display the QR-code as an image 
    def display(self):
        if not self.gen_flag:
            print("Cannot display the QR code!")
            return
        
        fig, ax = plt.subplots(1, 1, figsize=(14, 6))
        ax.axis('off')
        fig.subplots_adjust(left=0.25, right=0.75, top=0.75, bottom=0.25)
        qr_image = Image.fromarray(np.uint8(~self.qr_obj.mat) * 255)

        # Pad the image with whitespace
        padding = 6
        padded_image = Image.new('L', (qr_image.size[0] + 2 * padding, qr_image.size[1] + 2 * padding), 255)
        padded_image.paste(qr_image, (padding, padding))

        ax.imshow(padded_image, cmap='gray', vmin=0, vmax=255)
        plt.show()


    # Function to export the QR-code as an image 
    # The parameter fact determines the size of each module in pixels 
    def export(self, filename, scale=20):
        if not self.gen_flag:
            print("Cannot export the QR code!")
            return
        
        qr_image = Image.fromarray(np.uint8(~self.qr_obj.mat) * 255)

        # Scale the image by a factor of fact
        qr_image = qr_image.resize((qr_image.size[0] * scale, qr_image.size[1] * scale), Image.NEAREST)

        # Pad the image with whitespace (6 modules on each side, minimum required = 4 modules)
        padding = 6 * scale 
        padded_image = Image.new('L', (qr_image.size[0] + 2 * padding, qr_image.size[1] + 2 * padding), 255)
        padded_image.paste(qr_image, (padding, padding))
        padded_image.save(filename)
        print("QR code saved as", filename)
        return


    # Function to print various stats about the QR code
    def print_stats(self): 
        if not self.gen_flag:
            print("No stats to display!")
            return
        
        print("QR Code:")
        print("  Version =", self.version)
        print("  Data format =", self.DATATYPE_ID[self.dtype])
        print("  Error Correction Level =", self.EC_LEVEL_ID[self.errlvl])
        print("  String encoded =", self.msg)
        print() 
        print("  QR code size =", self.qr_obj.size, "x", self.qr_obj.size, "modules")
        print("  Number of preset modules =", self.qr_obj.num_func_bits)
        print("  Number of available modules =", self.qr_obj.size**2 - self.qr_obj.num_func_bits)
        print() 
        print("  Data length =", self.data_obj.num_databytes, "bytes =", 8*self.data_obj.num_databytes, "modules")
        print("  Allowed message length =", self.data_obj.num_msgbytes, "bytes =", 8*self.data_obj.num_msgbytes, "modules")
        print("  Length of encoded message =", self.msglen, "bytes")
        # print("  Number of error correction words =", self.num_databytes - self.num_msgbytes)
        # print("  Remainder = ", self.num_rembits, "modules")
        print()
        print("  Encoded using pattern mask number", self.qr_obj.masknum)

