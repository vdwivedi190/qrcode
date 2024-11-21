import numpy as np 
from .general import int_to_bool
from .errcorrection import append_version_ecbits

# Constants for the QR-code matrix
BLOCKLEN = 5       # Side length of the alignment block
CORNERLEN = 7      # Side length of the corner block


# Function to add the corner blocks to a given QR-code matrix
def add_corner(qrmat):
    # Define the corner block 
    cblock = np.zeros((CORNERLEN, CORNERLEN), dtype=bool)
    cblock[2:CORNERLEN-2, 2:CORNERLEN-2] = True         # Central square 
    cblock[0:CORNERLEN, 0] = True                       # Left vertical line
    cblock[0:CORNERLEN, CORNERLEN-1] = True             # Right vertical line
    cblock[0, 1:CORNERLEN-1] = True                     # Top horizontal line
    cblock[CORNERLEN-1, 1:CORNERLEN-1] = True           # Bottom horizontal line

    # Assign to the three corners of the QR-code matrix (excluding bottom-right corner) 
    qrmat[:CORNERLEN, :CORNERLEN] = cblock          # Top left 
    qrmat[:CORNERLEN,-CORNERLEN:] = cblock          # Top right 
    qrmat[-CORNERLEN:,:CORNERLEN] = cblock          # Bottom left 

    # Place the "dark module"
    qrmat[-CORNERLEN-1,CORNERLEN+1] = True
    

# Function to add the timing strip to a given QE-code matrix
def add_timing(qrmat):
    qrmat[CORNERLEN-1, CORNERLEN+1:-(CORNERLEN+1):2] = True   # Horizontal
    qrmat[CORNERLEN+1:-(CORNERLEN+1):2, CORNERLEN-1] = True   # Vertical 


# Function to initialize the mask for the non-data regions of the QR-code matrix
def init_fmask(mask,version):
    # Mask for the corner blocks 
    mask[:CORNERLEN+2, :CORNERLEN+2] = False         # Top left 
    mask[:CORNERLEN+2,-(CORNERLEN+1):] = False       # Top right
    mask[-(CORNERLEN+1):,:CORNERLEN+2] = False       # Bottom left

    # Mask for the version blocks 
    if version >= 7: 
        mask[-(CORNERLEN+4):-(CORNERLEN+1), :CORNERLEN-1] = False
        mask[:CORNERLEN-1,-(CORNERLEN+4):-(CORNERLEN+1)] = False

    # Mask for the timing strips 
    mask[CORNERLEN-1, CORNERLEN:-(CORNERLEN)] = False
    mask[CORNERLEN:-(CORNERLEN), CORNERLEN-1] = False


# Function to add the alignment blocks to the QR-code matrix and the mask matrix
def add_alignment(qrmat,mask,version,qrsize):    
    #  Define the alignment block of side length BLOCKLEN
    ablock = np.zeros((BLOCKLEN, BLOCKLEN), dtype=bool)
    ablock[2:-2, 2:-2] = True   # Central square 
    ablock[:, 0] = True     # Left vertical line
    ablock[:, -1] = True     # Right vertical line
    ablock[0, :] = True     # Top horizontal line
    ablock[-1, :] = True     # Bottom horizontal line

    n_algn = 1 + (version // 7)   # Number of alignment patterns - 1 
    
    # Compute the distance between the centers of the alignment patterns (counted from the right) 
    dist = np.ceil(0.5 * ( int(np.ceil((4*(version+1)/n_algn - 0.5) )))) 

    # Initialize the list of centers of the alignment patterns
    loc_list = np.zeros(n_algn+1, dtype=int)
    loc_list[0] = CORNERLEN-1

    # Compute the centers of the alignment patterns (starting from the rightmost end)
    for i in range(n_algn):
        loc_list[-i-1] = qrsize - CORNERLEN - 2*round(i*dist) 
    
    # Initialize the list of coordinates of the centers of the alignment patterns
    n_locs = (n_algn+1)**2 - 3     # Excluding three that overlap with the corner patterns
    coord_list = np.zeros((n_locs, 2), dtype=int)

    # Compute the centers of the alignment patterns (excluding the top row and left column)
    for i in range(n_algn):
        for j in range(n_algn):
            coord_list[i*n_algn + j] = [loc_list[-i-1], loc_list[-j-1]]

    # Compute the centers of the alignment patterns for top row and left column 
    # For both of these, the first and last elements overlap with the corner and must be excluded
    for i in range(1,n_algn):
        coord_list[n_algn**2 + i - 1] = [loc_list[i], loc_list[0]]
        coord_list[n_algn**2 + n_algn + i - 2] = [loc_list[0], loc_list[i]]
    
    # Assign the alignment blocks to the QR-code matrix and update the mask
    for x, y in coord_list:
        qrmat[x-2:x+3, y-2:y+3] = ablock
        mask[x-2:x+3, y-2:y+3] = False

    return n_algn


# Function to add the data (given as a boolean array) to the QR-code matrix
def add_data(qrmat, version, fmask, data):
    size = 4*version + 17

    # Start at the bottom-right corner of the qr_matrix
    pos = np.array([size-1, size-1],dtype=int)   

    # Index of the next bit in the data array to be placed in the QR-code matrix
    ind = 0              
    datalen = len(data) 

    # Movement vectors
    vx = np.array([0,-1])          # Horizontal (along the row) movement vector
    vy = np.array([-1,1])        # Diagonal movement vector
    vdir = -1             # Vertical direction of movement (+1 for down, -1 for up)
    hflag = True         # Flag to indicate horizontal movement  

    while True:
        # If all data bits have been placed in the QR-code matrix
        if ind == datalen:  
            break 

        # If the current position is at the top-left corner then we are done 
        if pos[0] == 0 and pos[1] == 0:
            break    
        
        # If the current position is in the timing strip, then skip one column to the left
        if pos[1] == CORNERLEN-1:        
            pos = pos + [0,-1]

        # If the current position is in the encoding region, then add the next bit
        if fmask[pos[0], pos[1]]:
            qrmat[pos[0], pos[1]] = data[ind]
            # print("Setting bit at ", pos, " to ", msg[ind])
            ind += 1  
        
        # Move along x or diagonally depending on the horizontal flag
        if hflag:
            nextpos = pos + [0,-1]
        else:
            nextpos = pos + [vdir,1]
        
        # Flip the horizontal flag (so that the next step is diagonal)
        hflag = not hflag

        # If the new position is outside the QR-code matrix, then change direction and move accordingly
        # If not then update the position
        if nextpos[0] < 0 or nextpos[0] >= size:
            pos = pos + [0,-1] 
            vdir = -vdir
            hflag = True
        else:
            pos = nextpos


# Function to place the format string in the QR-code matrix
def add_format(qrmat, fmt): 
    # Add around the top-left corner
    qrmat[CORNERLEN+1, :CORNERLEN-1] = fmt[:CORNERLEN-1]
    qrmat[CORNERLEN+1, CORNERLEN] = fmt[CORNERLEN-1]   
    qrmat[CORNERLEN+1, CORNERLEN+1] = fmt[CORNERLEN]   
    qrmat[CORNERLEN, CORNERLEN+1] = fmt[CORNERLEN+1]
    qrmat[CORNERLEN-2::-1, CORNERLEN+1] = fmt[CORNERLEN+2:]
       
    # Add a second copy next to bottom-left and top-right corners 
    qrmat[-1:-(CORNERLEN+1):-1, CORNERLEN+1] = fmt[:CORNERLEN]   
    qrmat[CORNERLEN+1,-(CORNERLEN+1):] = fmt[CORNERLEN:]


# Function to place the version string in the QR-code matrix
def add_version(qrmat, ver_arr):
    # Add near the top-right corner
    qrmat[:CORNERLEN-1,-CORNERLEN-2] = ver_arr[-3::-3]
    qrmat[:CORNERLEN-1,-CORNERLEN-3] = ver_arr[-2::-3]
    qrmat[:CORNERLEN-1,-CORNERLEN-4] = ver_arr[-1::-3]

    # Add near the bottom-left corner
    qrmat[-CORNERLEN-2, :CORNERLEN-1] = ver_arr[-3::-3]
    qrmat[-CORNERLEN-3, :CORNERLEN-1] = ver_arr[-2::-3]
    qrmat[-CORNERLEN-4, :CORNERLEN-1] = ver_arr[-1::-3]


# Function to compute the number of functional modules in the QR-code matrix
def compute_num_fmods(version, size, num_algn):     
    num_cornermods = 3*CORNERLEN**2 
    num_quietmods = 2*CORNERLEN+1
    num_darkmods = 1
    num_formatmods = 2*CORNERLEN+1

    # Need to double check this!!
    num_algnmods = num_algn*BLOCKLEN**2
    num_timemods = 2*(size - (2*CORNERLEN+3))

    if version >= 7:
        num_vermods = 3*(CORNERLEN-1)
    else:
        num_vermods = 0
    
    return num_cornermods + num_quietmods + num_darkmods + num_formatmods + num_algnmods + num_timemods + num_vermods
  


# Function to initialize the QR-code matrix and the mask matrix given the version
def initialize(version):
    # Compute the size of the QR-code matrix
    size = 4*version + 17

    # Initialize the QR-code matrix and the mask matrix for the functional regions
    # The entries fmask[i,j] == False if the module (i,j) is a functional module
    qrmat = np.zeros((size, size), dtype=bool)
    fmask = np.full((size, size), True, dtype=bool)

    # Add the corner blocks and timing strip to the QR-code matrix
    add_corner(qrmat) 
    add_timing(qrmat) 

    # Initialize the functional regions mask 
    init_fmask(fmask,version)

    # Add the alignment blocks: relevent only for versions > 1
    if version > 1:
        num_algn = add_alignment(qrmat, fmask, version, size)
        # The return value is the number of the alighment blocks 
    else:
        num_algn = 0

    # Add the version information to the QR-code matrix
    if version >= 7:        
        ver_arr = np.zeros(18, dtype=bool)   
        ver_arr[0:6] = int_to_bool(version,6) 
        append_version_ecbits(ver_arr)
        add_version(qrmat, ver_arr)

    # Compute the number of modules free for data and its error correction bits
    num_mods = size**2 
    num_freemods = num_mods - compute_num_fmods(version, size, num_algn)

    print("Initialized the QR-code matrix of version ", version)

    return qrmat, fmask, num_freemods