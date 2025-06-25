from .specification import QRspec

from .galois import GF_mult_poly, GF_div_poly, GF_antilogs


def compute_EC_blocks(spec: QRspec, data_blocks: list[list[int]]) -> list[list[int]]:
    """Adds error correction blocks to the data blocks."""
    EC_blocks = []
    EC_poly = construct_EC_poly(spec.EC_bytes_per_block)
    for data_block in data_blocks:
        EC_blocks.append(compute_EC_bytes(data_block, EC_poly))

    return EC_blocks


# Construct the polynomial for error correction of the data string
def construct_EC_poly(nblocks: int) -> list[int]:
    poly = [1, 1]
    for i in range(1, nblocks):
        poly = GF_mult_poly(poly, [1, GF_antilogs[i]])
    return poly


# Compute the error correction bytes for an integer array
# (equivalent to an array with elements in GF(2^8))
def compute_EC_bytes(data, EC_poly):
    datalen = len(data)
    EClen = len(EC_poly)
    tmp_coeffs: list[int] = [0] * (datalen + EClen - 1)
    tmp_coeffs[:datalen] = data
    return GF_div_poly(tmp_coeffs, EC_poly)[-len(EC_poly) :]
