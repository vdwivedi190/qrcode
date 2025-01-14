import numpy as np 

class QRmatrix:
    CORNER_SIZE = 7
    ALIGNMENT_BLOCKSIZE = 5

    # INITIALIZATION 
    # =================================================================
    def __init__(self, version):
        self.version = version
        self.size = 4*version + 17

        self.num_func_bits = 0 
        
        # Initialize the QR-code matrix and the mask matrix for the functional regions
        # For the latter, fmask[i,j] == False if the module (i,j) is a functional module
        self.mat = np.zeros((self.size, self.size), dtype=bool)
        self.fmask = np.full((self.size, self.size), True, dtype=bool)        
        
        # Add the corner and timing blocks
        self.num_func_bits += self.add_corner_and_timing() 

        # Alignment modules are required only for versions > 1
        if self.version > 1:
            self.num_func_bits += self.add_alignment_blocks() 

        # The format strip is added at the very end (since it contains the mask number)
        # Thus remove the number of bits added by the format strip "by hand"
        self.num_func_bits += 2 * (2*self.CORNER_SIZE+1)   # Format strip 

        # Generate the set of pattern masks for the given size
        self.pmasks = gen_pmasks(self.size) 


    # PLACMENT OF FUNCTIONAL MODULES IN THE QR-CODE MATRIX
    # =================================================================

    # Function to add the corner blocks to a given QR-code matrix
    # Returns the total number of modules occupied by the corner and timing blocks
    def add_corner_and_timing(self):
        crn_sz = self.CORNER_SIZE
        
        # Define the corner block 
        cblock = np.zeros((crn_sz, crn_sz), dtype=bool)
        cblock[2:crn_sz-2, 2:crn_sz-2] = True         # Central square 
        cblock[0:crn_sz, 0] = True                       # Left vertical line
        cblock[0:crn_sz, crn_sz-1] = True             # Right vertical line
        cblock[0, 1:crn_sz-1] = True                     # Top horizontal line
        cblock[crn_sz-1, 1:crn_sz-1] = True           # Bottom horizontal line

        # Assign to the three corners of the QR-code matrix (excluding bottom-right corner) 
        self.mat[:crn_sz, :crn_sz] = cblock          # Top left 
        self.mat[:crn_sz,-crn_sz:] = cblock          # Top right 
        self.mat[-crn_sz:,:crn_sz] = cblock          # Bottom left 

        # Place the "dark module"
        self.mat[-crn_sz-1,crn_sz+1] = True

        # Add the timing strips
        self.mat[crn_sz-1, crn_sz+1:-(crn_sz+1):2] = True   # Horizontal timing strip
        self.mat[crn_sz+1:-(crn_sz+1):2, crn_sz-1] = True   # Vertical timing strip 

        # Exclude the corner blocks, the surrounding quiet regions, and format strips from the functional region mask
        self.fmask[:crn_sz+2, :crn_sz+2] = False         # Top left 
        self.fmask[:crn_sz+2,-(crn_sz+1):] = False       # Top right
        self.fmask[-(crn_sz+1):,:crn_sz+2] = False       # Bottom left

        # Exclude the timing strips from the functional region mask
        self.fmask[crn_sz-1, crn_sz:-(crn_sz)] = False
        self.fmask[crn_sz:-(crn_sz), crn_sz-1] = False

        num_corner_bits = 3 * (crn_sz+1)**2 + 1   # Including the dark module
        num_timing_bits = 2*(self.size - 2*(crn_sz+1))   # Timing strips

        return num_corner_bits + num_timing_bits 

        
    # Function to add the alignment blocks 
    # Returns the total number of modules occupied by the alignment blocks
    def add_alignment_blocks(self):               

        crn_sz = self.CORNER_SIZE
        blk_sz = self.ALIGNMENT_BLOCKSIZE

        #  Define the alignment block of side length BLOCKLEN
        ablock = np.zeros((blk_sz, blk_sz), dtype=bool)
        ablock[2:-2, 2:-2] = True   # Central square 
        ablock[:, 0] = True     # Left vertical line
        ablock[:, -1] = True     # Right vertical line
        ablock[0, :] = True     # Top horizontal line
        ablock[-1, :] = True     # Bottom horizontal line

        nblocks_side = 2 + (self.version // 7)   # Number of alignment patterns per side

        # Compute the distance between the centers of the alignment patterns (counted from the right) 
        dist = np.ceil(0.5 * ( int(np.ceil((4*(self.version+1)/(nblocks_side-1) - 0.5) )))) 

        # Initialize the list of possible values for the center coordinates of the alignment patterns 
        loc_list = np.zeros(nblocks_side, dtype=int)
        loc_list[0] = crn_sz-1

        # Compute the centers of the alignment patterns (starting from the rightmost)
        for i in range(nblocks_side-1):
            loc_list[-i-1] = self.size - crn_sz - 2*round(i*dist) 

        # Initialize the list of coordinates of the centers of the alignment patterns
        num_alignment_blocks = nblocks_side**2 - 3     # Excluding three that overlap with the corner patterns
        coord_list = np.zeros((num_alignment_blocks, 2), dtype=int)

        # Index for the list of coordinates 
        ind = 0

        # Compute the centers of the alignment patterns (excluding the top row and left column)
        for i in range(nblocks_side-1):
            for j in range(nblocks_side-1):
                coord_list[ind] = [loc_list[-i-1], loc_list[-j-1]]
                ind += 1 

        # Compute the centers of the alignment patterns for top row and left column 
        # For both of these, the first and last elements overlap with the corner and must be excluded
        for i in range(1,nblocks_side-1):
            coord_list[ind] = [loc_list[i], loc_list[0]]
            coord_list[ind+1] = [loc_list[0], loc_list[i]]
            ind += 2

        # Assign the alignment blocks to the QR-code matrix and update the mask
        for x, y in coord_list:
            self.mat[x-2:x+3, y-2:y+3] = ablock
            self.fmask[x-2:x+3, y-2:y+3] = False

        # Compute the number of modules excluded by the alignment patterns
        num_alignment_bits = num_alignment_blocks * blk_sz**2

        # The nblocks_side-2 blocks overlap with the timing modules 
        # They must be removed to avoid double counting 
        num_alignment_bits -= 2*(nblocks_side-2)*blk_sz   
        
        return num_alignment_bits 


    # Function to add the version information to the bottom-left and top-right
    # corners of the QR-code (only relevant for versions 7 and above)
    def add_version_info(self, ver_arr):   
        # Define local var to avoid the clutter of having to write "self.CORNER_SIZE" everywhere
        crn_sz = self.CORNER_SIZE

        # Add near the top-right corner
        self.mat[:crn_sz-1,-crn_sz-2] = ver_arr[-3::-3]
        self.mat[:crn_sz-1,-crn_sz-3] = ver_arr[-2::-3]
        self.mat[:crn_sz-1,-crn_sz-4] = ver_arr[-1::-3]

        # Add near the bottom-left corner
        self.mat[-crn_sz-2, :crn_sz-1] = ver_arr[-3::-3]
        self.mat[-crn_sz-3, :crn_sz-1] = ver_arr[-2::-3]
        self.mat[-crn_sz-4, :crn_sz-1] = ver_arr[-1::-3]

        # Exclude the version blocks from the functional region mask
        self.fmask[:crn_sz-1,-crn_sz-4:-crn_sz-1] = False       # Top right
        self.fmask[-crn_sz-4:-crn_sz-1,:crn_sz-1] = False       # Bottom left

        # Return the number of modules occupied by the version blocks
        self.num_func_bits += 2*3*(crn_sz-1)
        return 2*3*(crn_sz-1)    
    

    # Function to place the format string in the QR-code matrix
    def add_format_info(self, fmt_arr): 
        # Define local var to avoid the clutter of having to write "self.CORNER_SIZE" everywhere
        crn_sz = self.CORNER_SIZE
        
        # Add around the top-left corner
        self.mat[crn_sz+1, :crn_sz-1] = fmt_arr[:crn_sz-1]
        self.mat[crn_sz+1, crn_sz] = fmt_arr[crn_sz-1]   
        self.mat[crn_sz+1, crn_sz+1] = fmt_arr[crn_sz]
        self.mat[crn_sz, crn_sz+1] = fmt_arr[crn_sz+1]   
        self.mat[crn_sz-2::-1, crn_sz+1] = fmt_arr[crn_sz+2:]
        
        # Add a second copy next to bottom-left and top-right corners 
        self.mat[-1:-(crn_sz+1):-1, crn_sz+1] = fmt_arr[:crn_sz]   
        self.mat[crn_sz+1, -(crn_sz+1):] = fmt_arr[crn_sz:]
        
        # Return the number of modules occupied by the format strip
        return 2 * (2*crn_sz+1) 



    # PLACMENT OF DATA ARRAY
    # =================================================================

    # Function to add the data (given as a boolean array) to the QR-code matrix
    def add_data(self, data):
        # Starting position (at the bottom-right corner of the matrix)
        pos = np.array([self.size-1, self.size-1],dtype=int)   
        
        # Movement vectors
        vx = np.array([0,-1])          # Horizontal (along the row) movement vector
        vy = np.array([-1,1])        # Diagonal movement vector
        vdir = -1             # Vertical direction of movement (+1 for down, -1 for up)
        hflag = True         # Flag to indicate horizontal movement  

        # Index of the next bit in the data array to be placed in the QR-code matrix
        ind = 0                      

        # Length of the data array
        datalen = len(data) 

        while True:
            # If all data bits have been placed in the QR-code matrix
            if ind == datalen:  
                break 

            # If the current position is at the top-left corner then we are done 
            if pos[0] == 0 and pos[1] == 0:
                break    
            
            # If the current position is in the timing strip, then skip one column to the left
            if pos[1] == self.CORNER_SIZE-1:        
                pos = pos + [0,-1]

            # If the current position is in the encoding region, then add the next bit
            if self.fmask[pos[0], pos[1]]:
                self.mat[pos[0], pos[1]] = data[ind]
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
            if nextpos[0] < 0 or nextpos[0] >= self.size:
                pos = pos + [0,-1] 
                vdir = -vdir
                hflag = True
            else:
                pos = nextpos



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

