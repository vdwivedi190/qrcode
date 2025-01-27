import numpy as np 
from PIL import Image
import matplotlib.pyplot as plt

from .QRmatrix import QRmatrix
from .QRdata import QRdata, DATASPEC_FILE

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
    def __init__(self, msg, version=None, dtype=2, errcode='M'):
        # Check if the QR code has been generated (Useful for the display/export functions)
        self.msg = msg
        self.msglen = len(msg)

        if type(dtype) != int:
            raise TypeError("Data type must be an integer!")            
        elif dtype not in [0,1,2]:
            raise ValueError("Invalid data type!")
        else:
            self.dtype = dtype

        if errcode not in ['L', 'M', 'Q', 'H']:
            raise ValueError("The valid error correction levels are 'L', 'M', 'Q', and 'H'!")
        else:
            self.errlvl = self.EC_LEVEL_CODE[errcode]

        if version == None:
            self.version = self.lookup_datasize()
        elif type(version) != int:
            raise TypeError("The version must be an integer!")    
        elif version < 1 or version > self.MAX_VERSION:
            raise ValueError("The version must be an integer between 1 and" + str(self.MAX_VERSION) + "!")
        else:
            self.version = version


    def generate(self):
        if self.msglen > self.MAX_CAPACITY[self.dtype]:
            raise ValueError("Message too long for the given data type!")

        self.data_obj = QRdata(self.version, self.dtype, self.errlvl)

        # Check if the message is too long for the given version
        if self.data_obj.num_msgbytes < self.msglen:
            raise ValueError("Message too long for the given data type!")
        
        self.data_obj.encode(self.msg)
        self.data = self.data_obj.data

        # Initialize a QRmatrix object 
        self.qr_obj = QRmatrix(self.version, self.errlvl)

        # Add to the QR code matrix 
        self.qr_obj.add_data(self.data_obj.data)
        self.qr_obj.pattern_mask()

        self.qrmat = self.qr_obj.mat


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
        if not hasattr(self, 'qrmat'):
            return "QR code not generated!"
        return "Encoded message = " + self.msg
    
    
    # Function to display the QR-code as an image 
    def display(self):
        if not hasattr(self, 'qrmat'):
            self.generate()
            
        fig, ax = plt.subplots(1, 1, figsize=(14, 6))
        ax.axis('off')
        fig.subplots_adjust(left=0.25, right=0.75, top=0.75, bottom=0.25)
        qr_image = Image.fromarray(np.uint8(~self.qrmat) * 255)

        # Pad the image with whitespace
        padding = 6
        padded_image = Image.new('L', (qr_image.size[0] + 2 * padding, qr_image.size[1] + 2 * padding), 255)
        padded_image.paste(qr_image, (padding, padding))

        ax.imshow(padded_image, cmap='gray', vmin=0, vmax=255)
        plt.show()


    # Function to export the QR-code as an image 
    # The parameter fact determines the size of each module in pixels 
    def export(self, filename, scale=20):
        if not hasattr(self, 'qrmat'):
            self.generate()
        
        qr_image = Image.fromarray(np.uint8(~self.qrmat) * 255)

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
        if not hasattr(self, 'qrmat'):
            self.generate()
        
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
        print()
        print("  Encoded using pattern mask number", self.qr_obj.masknum)

