import numpy as np 

"""
This module contains functions related to the pattern masking in the QR code standard.
"""

# Constant penalty factors (as per the QR code standard) required for pattern masking
RUN_FACTOR = 3 
BLOCK_FACTOR = 3
CORNER_FACTOR = 40
HOM_FACTOR = 10

# The pattern of dark/light modules in the corners of the QR code matrix
# The existence of this pattern elsewhere in the matrix is penalized
CORNER_PATTERN = np.bool_([1,0,1,1,1,0,1,0,0,0,0])
PATTERN_LEN = 11


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


# Function to evaluate the total penalty for a given QR matrix
def eval_qrmat(mat, len):
    # Initialize the penalty to zero
    penalty = 0 

    # Check for runs of more than five consecutive dark/light modules
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

    # Check for patterns of dark/light modules resembling the corners
    for i in range(0, len):
        for j in range(0, len-PATTERN_LEN):
            penalty += CORNER_FACTOR * count_matches(mat[i,j:j+PATTERN_LEN], CORNER_PATTERN)
            penalty += CORNER_FACTOR * count_matches(mat[j:j+PATTERN_LEN, i], CORNER_PATTERN)

    # Check for deviation from a 50-50 distribution of dark modules
    darkmod_count = np.sum(mat)
    darkmod_frac = darkmod_count / (len*len)
    penalty += np.uint8(np.floor(abs(darkmod_frac - 0.5))) * HOM_FACTOR 
    
    return penalty


# Function to count the number of times the string "pattern" appears in the vector "vec" 
# This includes overlaps and forward as well as backward matches
def count_matches(vec, pattern):
    count = 0 
    for i in range(len(vec)-len(pattern)+1):
        if np.all(vec[i:i+len(pattern)] == pattern):
            count += 1
        if np.all(vec[i:i+len(pattern)] == pattern[::-1]):
            count += 1
    return count