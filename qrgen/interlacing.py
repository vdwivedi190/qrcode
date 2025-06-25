import logging

from .specification import QRspec
from .utils import int_to_bool


logger = logging.getLogger(__name__)


def split_data_in_blocks(data: list[int], spec: QRspec) -> list[list[int]]:
    """Splits the data into blocks according to the QR code specification."""

    data_blocks = []
    ind = 0
    for block_datalen in spec.block_list:
        data_blocks.append(data[ind : (ind + block_datalen)])
        ind += block_datalen
    return data_blocks


def interlace_blocks(
    spec: QRspec, data_blocks: list[list[int]], EC_blocks: list[list[int]]
) -> list[int]:
    """Interlaces the data blocks and error correction blocks according to the QR code specification."""
    ind = 0

    result: list[int] = [0] * spec.capacity_in_bytes
    ind = 0

    total_num_blocks = sum(spec.num_blocks)

    # If all message blocks have the same length, then read the blocks columnwise
    if len(spec.num_blocks) == 1:
        for coeff in range(spec.datalen_per_block[0]):
            for block in range(total_num_blocks):
                result[ind] = data_blocks[block][coeff]
                ind += 1

    # If the blocks have different lengths, then the (longer) second set of blocks
    # must be treated differently
    elif len(spec.num_blocks) == 2:
        for coeff in range(min(spec.datalen_per_block)):
            for block in range(total_num_blocks):
                result[ind] = data_blocks[block][coeff]
                ind += 1

        for block in range(spec.num_blocks[1]):
            result[ind] = data_blocks[spec.num_blocks[0] + block][-1]
            ind += 1

    else:
        raise ValueError("Only expected two kinds of blocks, but got more than two!")

    logger.debug(
        f"Interlacing {len(data_blocks)} data blocks and {len(EC_blocks)} error correction blocks..."
    )

    # The error correction blocks are all of the same length
    for coeff in range(spec.EC_bytes_per_block):
        for block in range(total_num_blocks):
            result[ind] = EC_blocks[block][coeff]
            ind += 1

    return result


def bits_from_blocks(data: list[int]) -> list[bool]:
    """Converts a list of blocks (each block is a list of integers) into a flat list of bits."""
    result = []
    for i in data:
        result.extend(int_to_bool(i, 8))
    return result
