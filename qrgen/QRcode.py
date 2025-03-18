import numpy as np 
from PIL import Image
import matplotlib.pyplot as plt

from .QRmatrix import QRmatrix
from .QRdata import QRdata, MAX_VERSION

class QRcode:
        
    DATATYPE_ID = {0:'Numeric', 1:'Alphanumeric', 2:'Binary'}    
    MAX_CAPACITY = {0:7089, 1:4296, 2:2953}

    EC_LEVEL_ID = {0:'M', 1:'L', 2:'H', 3:'Q'}
    EC_LEVEL_CODE = {'L':1, 'M':0, 'Q':3, 'H':2}
    
    # Default encoding = binary 
    # Default error correction level = M
    # If a version number is not provided, then it is computed based on the length of the message

    def __init__(self, msg:str="", version:int=None, dtype:int=2, errcode:chr='M'):
        self.msg = msg
        self.msglen = len(msg)

        if type(dtype) != int:
            raise TypeError(f"{dtype} is not a valid data type; integer expected!")            
        elif dtype not in [0,1,2]:
            raise ValueError(f"{dtype} is not a valid data type; only 0-3 expected!")
        elif dtype == 3:
            raise NotImplementedError("Kanji mode (Data type 3) not supported!")
        else:
            self.dtype = dtype

        if errcode not in ['L', 'M', 'Q', 'H']:
            raise ValueError(f"{errcode} is not a valid error correction levels! Expected values are 'L', 'M', 'Q', or 'H'!")
        else:
            self.errlvl = self.EC_LEVEL_CODE[errcode]

        if version == None:
            self.version = None
        elif type(version) != int:
            raise TypeError(f"{version} is not a valid version number; integer expected!")
        elif version < 1 or version > MAX_VERSION:
            raise ValueError(f"The version must be an integer between 1 and {MAX_VERSION}!")
        else:
            self.version = version


    def generate(self) -> None:
        if self.msglen > self.MAX_CAPACITY[self.dtype]:
            raise ValueError("Message too long for the given data type!")

        self.data_obj = QRdata(self.version, self.dtype, self.errlvl)

        self.data_obj.encode(self.msg)

        if self.version is None:
            self.version = self.data_obj.version
        self.data = self.data_obj.data

        # Add to the QR code matrix 
        self.qr_obj = QRmatrix(self.version, self.errlvl)
        self.qr_obj.add_data(self.data_obj.data)
        self.qr_obj.pattern_mask()
        self.qrmat = self.qr_obj.mat

        # Generate the QR code image (with white padding)
        padding = 6
        self.tmp_img = Image.fromarray(np.uint8(~self.qrmat) * 255)
        width, height = self.tmp_img.size

        # The mode 'L' is for a 8-bit grayscale image
        self.qrimg = Image.new(mode='L', size=(width + 2 * padding, height + 2 * padding), color=255)
        self.qrimg.paste(self.tmp_img, (padding, padding))



    # PRINTING ROUNTINES
    # =================================================================

    def __str__(self):
        if not hasattr(self, 'qrmat'):
            return "QR code not generated!"
        return "Encoded message = " + self.msg
    
    
    # Function to display the QR-code as an image 
    def display(self):
        if not hasattr(self, 'qrimg'):
            self.generate()            
        
        fig, ax = plt.subplots(1, 1, figsize=(14, 6))
        ax.axis('off')
        fig.subplots_adjust(left=0.25, right=0.75, top=0.75, bottom=0.25)
        ax.imshow(self.qrimg, cmap='gray', vmin=0, vmax=255)
        plt.show()


    # Function to return the QR-code as an image 
    def get_image(self) -> Image:
        if not hasattr(self, 'qrimg'):
            self.generate()
            
        return self.qrimg


    # Function to export the QR-code as an image 
    # The parameter scale determines the size of each module in pixels 
    def export(self, filename:str, scale:int=20) -> None:
        if not hasattr(self, 'qrimg'):
            self.generate()
        
        width, height = self.qrimg.size
        resized_img = self.qrimg.resize((width*scale, height*scale), resample=Image.NEAREST)

        try:
            resized_img.save(filename)
        except ValueError:
            resized_img.save(filename, format="png")
            raise ValueError("Could not determine format from extension; using PNG instead")
        except OSError:
            raise Exception("Error saving the QR code as", filename)
    


    # Function to print various stats about the QR code
    def get_stats(self) -> dict: 
        if not hasattr(self, 'qrmat'):
            self.generate()

        stats = {}
        stats['version'] = self.version
        stats['encoding'] = self.DATATYPE_ID[self.dtype]
        stats['ec_level'] = self.EC_LEVEL_ID[self.errlvl]
        stats['masknum'] = self.qr_obj.masknum

        stats['qr_size'] = self.qr_obj.size
        stats['num_func_mods'] = self.qr_obj.num_func_bits
        stats['num_data_mods'] = self.qr_obj.size**2 - self.qr_obj.num_func_bits
        stats['num_data_words'] = self.data_obj.num_databytes
        stats['num_msg_words'] = self.data_obj.num_msgbytes

        stats['message'] = self.msg
        stats['message_length'] = self.msglen

        return stats 