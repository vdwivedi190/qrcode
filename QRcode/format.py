import numpy as np 
from .populate import CORNERLEN
from .populate import add_format, add_version
from .errcorrection import append_format_ecbits, append_version_ecbits
from .general import int_to_bool

# Function to generate the format string for a given error level and mask number
def gen_format_arr(errlvl, masknum):
    # Initialize the format string
    fmt = np.zeros(2*CORNERLEN+1, dtype=bool)   

    # The first two bits are the error correction level
    fmt[0:2] = int_to_bool(errlvl,2) 
    
    # The next three bits are the mask pattern number      
    fmt[2:5] = int_to_bool(masknum,3)      

    # Add the error correction bits to the format string
    append_format_ecbits(fmt)

    return fmt 


# Function to generate the pattern masks for a given size
def gen_pmasks(size):
    #  Initialize a 3d array to hold all masks for a given size 
    pmasks = np.zeros((8,size,size), dtype=bool)

    # Loop over all the modules in the QR-code matrix
    for i in range(size):
        for j in range(size):
            pmasks[0,i,j] = (i+j) % 2 == 0
            pmasks[1,i,j] = i % 2 == 0
            pmasks[2,i,j] = j % 3 == 0
            pmasks[3,i,j] = (i+j) % 3 == 0
            pmasks[4,i,j] = (i//2 + j//3) % 2 == 0
            pmasks[5,i,j] = (i*j) % 2 + (i*j) % 3 == 0
            pmasks[6,i,j] = ((i*j) % 2 + (i*j) % 3) % 2 == 0
            pmasks[7,i,j] = ((i+j) % 2 + (i*j) % 3) % 2 == 0
    return pmasks


def score_mask(qrmat):
    # Need to complete this function
    return 0


def pattern_mask(qrmat, version, errlvl, fmask):
    # Generate pattern masks
    size = 4*version + 17
    pmasks = gen_pmasks(size)

    # We start by masking with pattern 0
    fmt = gen_format_arr(errlvl, 0)
    best_qrmat = np.copy(qrmat)
    
    # Add the format string (consisting of format and mask number) to the QR-code matrix 
    add_format(best_qrmat, fmt)

    # Apply the pattern mask to the QR-code matrix
    combined_mask = np.logical_and(fmask, pmasks[0])
    np.logical_xor(best_qrmat, combined_mask, out=best_qrmat)

    # Evaluate the score of the masked QR-code matrix
    high_score = score_mask(best_qrmat) 

    for masknum in range(1,7): 
        cur_qrmat = np.copy(qrmat)
        fmt = gen_format_arr(errlvl, masknum)
        add_format(cur_qrmat, fmt)
        
        # Apply the pattern mask to the current QR-code matrix
        combined_mask = np.logical_and(fmask, pmasks[masknum])
        np.logical_xor(cur_qrmat, combined_mask, out=cur_qrmat)
        
        cur_score = score_mask(cur_qrmat)

        # If the current mask is better that the previous best, then update the best mask
        if high_score < cur_score:
            high_score = cur_score
            best_qrmat = cur_qrmat

    qrmat = best_qrmat
    return high_score