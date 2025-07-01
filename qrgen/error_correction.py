from .galois import GF_mult_poly, GF_div_poly, GF_antilogs


def compute_EC_blocks(
    EC_bytes_per_block: int, data_blocks: list[list[int]]
) -> list[list[int]]:
    """Adds error correction blocks to the data blocks."""
    EC_blocks = []
    EC_poly = construct_EC_poly(EC_bytes_per_block)
    for data_block in data_blocks:
        EC_blocks.append(compute_error_correction_bytes(data_block, EC_poly))

    return EC_blocks


def construct_EC_poly(nblocks: int) -> list[int]:
    """Construct the error correction polynomial for the given number of blocks."""
    poly = [1, 1]
    for i in range(1, nblocks):
        poly = GF_mult_poly(poly, [1, GF_antilogs[i]])
    return poly


def compute_error_correction_bytes(data, EC_poly):
    """Compute the error correction codewords for the given data using the given polynomial."""
    datalen = len(data)
    EClen = len(EC_poly)
    tmp_coeffs: list[int] = [0] * (datalen + EClen - 1)
    tmp_coeffs[:datalen] = data
    return GF_div_poly(tmp_coeffs, EC_poly)[-len(EC_poly) :]


def _find_next_nonzero(arr: list[bool]) -> int:
    """Find the index of the first True element in a boolean array.

    If no True element is found, return the length of the array.
    """
    for ind, elem in enumerate(arr):
        if elem:
            return ind
    else:
        return len(arr)


def compute_error_correction_bits(
    msg_coeffs: list[bool], EC_coeffs: list[bool]
) -> list[bool]:
    """Compute the error correction bits for the given message and error correction coefficients."""
    msg_len = len(msg_coeffs)
    ec_len = len(EC_coeffs)
    total_len = msg_len + ec_len - 1

    result = [False] * total_len
    result[:msg_len] = msg_coeffs

    start = _find_next_nonzero(result)
    while start + ec_len <= total_len:
        for ind in range(ec_len):
            result[start + ind] ^= EC_coeffs[ind]
        start = _find_next_nonzero(result)

    return list(result[-ec_len + 1 :])
