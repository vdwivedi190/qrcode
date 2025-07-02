import numpy as np

from .spec import QRspec, CORNER_SIZE, ALIGNMENT_BLOCK_SIZE
from .pattern_mask import eval_qrmat, gen_pmasks


class QRmatrix:
    """Class for generating the QR-code matrix.

    This class handles the generation of the QR-code matrix given a boolean array containing the
    data encoded as per the QR-code standard. It places all the functional modules in the QR-code
    matrix and generates and places the version information. Finally, it applies the optimal pattern
    mask to the QR-code matrix.
    """

    # =================================================================
    def __init__(self, spec: QRspec):
        self._spec = spec

        # Compute the size of the QR-code matrix as defined in the specifications
        self.size = 4 * self._spec.version + 17
        self.num_func_bits = 0

        # Initialize the QR-code matrix and the mask matrix for the functional regions
        # These are defined as numpy matrices of booleans (instead of lists of lists)
        # since that allows for setting submatrices to a constant value
        self.mat = np.full((self.size, self.size), False, dtype=bool)
        self.func_mask = np.full((self.size, self.size), True, dtype=bool)
        # We will set fmask[i,j] == False if the module (i,j) is a functional module

        self.num_func_bits += self._add_corner_and_timing()
        self.num_func_bits += self._add_alignment_blocks()
        if self._spec.version >= 7:
            ver_arr = np.array(self._spec.version_to_bool_array())
            self.num_func_bits += self._add_version_info(ver_arr)

        # The format strip is added at the very end (since it contains the mask number)
        # Thus remove the number of bits added by the format strip "by hand"
        self.num_func_bits += 2 * (2 * CORNER_SIZE + 1)  # Format strip

        # Generate the set of pattern masks for the given size
        self.pmasks = gen_pmasks(self.size)

    # PLACMENT OF FUNCTIONAL MODULES
    # =================================================================

    def _add_corner_and_timing(self) -> int:
        """Place the corner blocks and the timing strips in the QR-code matrix.

        Returns the total number of modules occupied by the corner and timing blocks.
        """

        # Initialize the corner block
        cblock = np.zeros((CORNER_SIZE, CORNER_SIZE), dtype=bool)
        cblock[2 : CORNER_SIZE - 2, 2 : CORNER_SIZE - 2] = True  # Central square
        cblock[0:CORNER_SIZE, 0] = True  # Left vertical line
        cblock[0:CORNER_SIZE, CORNER_SIZE - 1] = True  # Right vertical line
        cblock[0, 1 : CORNER_SIZE - 1] = True  # Top horizontal line
        cblock[CORNER_SIZE - 1, 1 : CORNER_SIZE - 1] = True  # Bottom horizontal line

        # Assign to the three corners of the QR-code matrix (excluding bottom-right corner)
        self.mat[:CORNER_SIZE, :CORNER_SIZE] = cblock  # Top left
        self.mat[:CORNER_SIZE, -CORNER_SIZE:] = cblock  # Top right
        self.mat[-CORNER_SIZE:, :CORNER_SIZE] = cblock  # Bottom left

        # Place the "dark module"
        self.mat[-CORNER_SIZE - 1, CORNER_SIZE + 1] = True

        # Add the timing strips
        self.mat[CORNER_SIZE - 1, CORNER_SIZE + 1 : -(CORNER_SIZE + 1) : 2] = (
            True  # Horizontal timing strip
        )
        self.mat[CORNER_SIZE + 1 : -(CORNER_SIZE + 1) : 2, CORNER_SIZE - 1] = (
            True  # Vertical timing strip
        )

        # Exclude the corner blocks, the surrounding quiet regions, and
        # format strips from the functional region mask
        self.func_mask[: CORNER_SIZE + 2, : CORNER_SIZE + 2] = False  # Top left
        self.func_mask[: CORNER_SIZE + 2, -(CORNER_SIZE + 1) :] = False  # Top right
        self.func_mask[-(CORNER_SIZE + 1) :, : CORNER_SIZE + 2] = False  # Bottom left

        # Exclude the timing strips from the functional region mask
        self.func_mask[CORNER_SIZE - 1, CORNER_SIZE:-(CORNER_SIZE)] = False
        self.func_mask[CORNER_SIZE:-(CORNER_SIZE), CORNER_SIZE - 1] = False

        num_corner_bits = 3 * (CORNER_SIZE + 1) ** 2 + 1  # Including the dark module
        num_timing_bits = 2 * (self.size - 2 * (CORNER_SIZE + 1))  # Timing strips

        return num_corner_bits + num_timing_bits

    def _compute_alignment_block_centers(self, num_per_side: int) -> np.ndarray:
        """Compute the centers of the alignment blocks in the QR-code matrix."""

        # Distance between the centers of the alignment patterns (counted from the right)
        dist = np.ceil(
            0.5
            * (int(np.ceil((4 * (self._spec.version + 1) / (num_per_side - 1) - 0.5))))
        )

        # Compute the allowed (x or y) coordinates for the centers of the alignment patterns
        coord_list = [0] * num_per_side
        coord_list[0] = CORNER_SIZE - 1
        for i in range(num_per_side - 1):
            coord_list[-i - 1] = self.size - CORNER_SIZE - 2 * round(i * dist)

        # Exclude three alignment blocks that overlap with the corner patterns
        num_alignment_blocks = num_per_side**2 - 3
        centers = np.zeros((num_alignment_blocks, 2), dtype=int)
        index = 0

        # Compute the centers of the alignment patterns (excluding the top row and left column)
        for i in range(num_per_side - 1):
            for j in range(num_per_side - 1):
                centers[index] = [coord_list[-i - 1], coord_list[-j - 1]]
                index += 1

        # Compute the centers of the alignment patterns for top row and left column
        # For both of these, the first and last elements overlap with the corner and must be excluded
        for i in range(1, num_per_side - 1):
            centers[index] = [coord_list[i], coord_list[0]]
            centers[index + 1] = [coord_list[0], coord_list[i]]
            index += 2

        return centers

    def _add_alignment_blocks(self) -> int:
        """Place the alignment blocks in the QR-code matrix.

        Returns the total number of modules occupied by the corner and timing blocks.
        """
        if self._spec.version < 2:
            return 0  # No alignment patterns for versions < 2

        # Number of alignment patterns per side
        num_blocks_per_side = 2 + (self._spec.version // 7)
        alignment_pattern_centers = self._compute_alignment_block_centers(
            num_blocks_per_side
        )

        #  Define the alignment block
        ablock = np.zeros((ALIGNMENT_BLOCK_SIZE, ALIGNMENT_BLOCK_SIZE), dtype=bool)
        ablock[2:-2, 2:-2] = True  # Central square
        ablock[:, 0] = True  # Left vertical line
        ablock[:, -1] = True  # Right vertical line
        ablock[0, :] = True  # Top horizontal line
        ablock[-1, :] = True  # Bottom horizontal line

        # Assign the alignment blocks to the QR-code matrix and update the mask
        for x, y in alignment_pattern_centers:
            self.mat[x - 2 : x + 3, y - 2 : y + 3] = ablock
            self.func_mask[x - 2 : x + 3, y - 2 : y + 3] = False

        # Compute the number of modules occupied by the alignment patterns
        num_alignment_bits = len(alignment_pattern_centers) * ALIGNMENT_BLOCK_SIZE**2
        # Remove the bits that overlap with the timing modules to avoid double counting
        num_alignment_bits -= 2 * (num_blocks_per_side - 2) * ALIGNMENT_BLOCK_SIZE
        return num_alignment_bits

    def _add_version_info(self, version_arr: np.ndarray) -> int:
        """Place the version information in the QR-code matrix.

        Returns the total number of modules occupied by the version blocks
        """
        # Top-right corner
        self.mat[: CORNER_SIZE - 1, -CORNER_SIZE - 2] = version_arr[-3::-3]
        self.mat[: CORNER_SIZE - 1, -CORNER_SIZE - 3] = version_arr[-2::-3]
        self.mat[: CORNER_SIZE - 1, -CORNER_SIZE - 4] = version_arr[-1::-3]

        # Bottom-left corner
        self.mat[-CORNER_SIZE - 2, : CORNER_SIZE - 1] = version_arr[-3::-3]
        self.mat[-CORNER_SIZE - 3, : CORNER_SIZE - 1] = version_arr[-2::-3]
        self.mat[-CORNER_SIZE - 4, : CORNER_SIZE - 1] = version_arr[-1::-3]

        # Exclude the version blocks from the functional region mask
        self.func_mask[: CORNER_SIZE - 1, -CORNER_SIZE - 4 : -CORNER_SIZE - 1] = False
        self.func_mask[-CORNER_SIZE - 4 : -CORNER_SIZE - 1, : CORNER_SIZE - 1] = False

        return 2 * 3 * (CORNER_SIZE - 1)

    def _add_format_info(self, fmt_arr: np.ndarray) -> int:
        """Place the format information in the QR-code matrix.

        Returns the total number of modules occupied by the version blocks
        """
        # Top-left corner
        self.mat[CORNER_SIZE + 1, : CORNER_SIZE - 1] = fmt_arr[: CORNER_SIZE - 1]
        self.mat[CORNER_SIZE + 1, CORNER_SIZE] = fmt_arr[CORNER_SIZE - 1]
        self.mat[CORNER_SIZE + 1, CORNER_SIZE + 1] = fmt_arr[CORNER_SIZE]
        self.mat[CORNER_SIZE, CORNER_SIZE + 1] = fmt_arr[CORNER_SIZE + 1]
        self.mat[CORNER_SIZE - 2 :: -1, CORNER_SIZE + 1] = fmt_arr[CORNER_SIZE + 2 :]

        # Add a second copy next to bottom-left and top-right corners
        self.mat[-1 : -(CORNER_SIZE + 1) : -1, CORNER_SIZE + 1] = fmt_arr[:CORNER_SIZE]
        self.mat[CORNER_SIZE + 1, -(CORNER_SIZE + 1) :] = fmt_arr[CORNER_SIZE:]

        return 2 * (2 * CORNER_SIZE + 1)

    # PLACMENT OF THE DATA IN THE QR-CODE MATRIX
    # =================================================================

    def add_data(self, data) -> None:
        """
        Place the data in the QR-code matrix.

        The assignment of data modules follows by moving a "cursor" in a ziazag fashion
        as specified in the QR-code standard, while avoiding the functional regions.
        The cursor starts at the bottom-right corner and moves upwards, alternating between
        horizontal and diagonal movements, whose directions are stored in vectors vx and vy.
        Once the cursor reaches the top edge, it shifts to the left and starts moving downwards.
        This general up/down trend is indicated by vdir (+1 for down, -1 for up)
        """

        # Define the step vectors for horizontal and vertical movements
        # Diagonal movement is obtained by combining the horizontal and vertical movements
        STEP_LEFT = np.array([0, -1])
        STEP_RIGHT = np.array([0, 1])
        STEP_UP = np.array([-1, 0])

        # Flags for the direction of movement
        vdir = 1  # 1 for up, -1 for down
        hflag = True  # True for horizontal, False for diagonal movement

        # Starting position (at the bottom-right corner of the matrix)
        # The position is given as [row, column], equivalent to [y, x] in Cartesian coordinates
        # The top-left corner is at pos = [0,0]
        pos = np.array([self.size - 1, self.size - 1])

        datalen = len(data)
        index = 0  # Indexes the bit in the data array to be placed
        while index < datalen:
            # If the current position is in the encoding region, then add the next bit
            if self.func_mask[pos[0], pos[1]]:
                self.mat[pos[0], pos[1]] = data[index]
                index += 1

            # If the current position is in the timing strip
            if pos[1] == CORNER_SIZE - 1:
                pos = pos + STEP_LEFT

            # Compute the next position (horizontal or diagonal) based on hflag
            # and flip hflag to alternate between the two directions of motion
            if hflag:
                nextpos = pos + STEP_LEFT
            else:
                nextpos = pos + STEP_RIGHT + vdir * STEP_UP
            hflag = not hflag

            # If the computed next position is outside the QR-code matrix, then change direction
            if nextpos[0] < 0 or nextpos[0] >= self.size:
                pos = pos + STEP_LEFT
                vdir *= -1
                hflag = True
            else:
                pos = nextpos

    # PATTERN MASKING
    # =================================================================

    def pattern_mask(self) -> None:
        """Apply the optimal pattern mask to the QR-code matrix."""

        # Initialize the max_penalty to something large
        max_penalty = 100000
        best_mask_num = -1
        best_qrmat = self.mat.copy()

        # Iterate over all possible mask patterns
        for mask_num in range(0, 8):
            # Add the format information array for the current mask number
            format_arr = np.array(self._spec.format_to_bool_array(mask_num))
            self._add_format_info(format_arr)

            # Copy the current QR code matrix
            cur_qrmat = self.mat.copy()

            # Apply the pattern mask to the current QR code matrix
            combined_mask = np.logical_and(self.func_mask, self.pmasks[mask_num])
            np.logical_xor(cur_qrmat, combined_mask, out=cur_qrmat)

            # Score the current QR code matrix
            penalty = eval_qrmat(cur_qrmat, self.size)

            # Update the best QR matrix and score if the current score is better
            if penalty < max_penalty:
                max_penalty = penalty
                best_mask_num = mask_num
                best_qrmat = cur_qrmat

        # Set the QR code matrix to the best one found
        self.masknum = best_mask_num
        self.mat = best_qrmat

        return
