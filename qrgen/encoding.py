import logging
from string import ascii_uppercase

from .spec import QRspec, Encoding
from .utils import int_to_bool_list, binary_to_int

logger = logging.getLogger(__name__)

_ALPHANUM_NUMBER_CODES = {str(digit): digit for digit in range(10)}
_ALPHANUM_LETTER_CODES = {char: ord(char) - 55 for char in ascii_uppercase}
_ALPHANUM_SYMBOL_CODES = {
    " ": 36,
    "$": 37,
    "%": 38,
    "*": 39,
    "+": 40,
    "-": 41,
    ".": 42,
    "/": 43,
    ":": 44,
}
_ALPHANUM_CODES = (
    _ALPHANUM_NUMBER_CODES | _ALPHANUM_LETTER_CODES | _ALPHANUM_SYMBOL_CODES
)


def encode(spec: QRspec, msg: str) -> list[int]:
    """Encodes the message in the specified QR code specification and data type.

    Args:
        spec (QRspec): The QR code specification.
        msg (str): The message to encode.
        dtype (int): The data type (0 for numeric, 1 for alphanumeric, 2 for binary).

    Returns:
        list[int]: The encoded message as a list of integers.
    """

    match spec.encoding:
        case Encoding.NUMERIC:
            logger.debug("Numerical encoding...")
            encoded_msg = _qr_encode_numeric(msg)
        case Encoding.ALPHANUMERIC:
            logger.info("Converting to uppercase for alphanumeric encoding...")
            encoded_msg = _qr_encode_alphanumeric(msg.upper())
        case Encoding.BINARY:
            logger.debug("Binary encoding...")
            encoded_msg = _qr_encode_binary(msg)
        case Encoding.KANJI:
            raise NotImplementedError(
                "Kanji encoding is not implemented in this package!"
            )

    encoding_header = spec.encoding.get_code()
    msglen_header = int_to_bool_list(len(msg), spec.num_msglen_bits)
    # Encode the length of the message in the specified number of bits

    header = encoding_header + msglen_header

    data = header + encoded_msg
    pad_data(data, spec.datalen_in_bits)

    return [binary_to_int(data[i : i + 8]) for i in range(0, len(data), 8)]


def _qr_encode_binary(msg: str) -> list[bool]:
    """Encode a string in binary mode"""
    result: list[bool] = []
    for char in msg:
        result.extend(int_to_bool_list(ord(char), 8))

    return result


def _qr_encode_numeric(msg: str) -> list[bool]:
    """Encode a string in alphanumeric mode"""
    if not msg.isdecimal():
        raise ValueError(
            "Cannot use numeric encoding, since the message contains non-numeric characters!"
        )

    result: list[bool] = []

    # Number of complete 2-character blocks
    num_triplets = len(msg) // 3
    num_remaining = len(msg) % 2

    # Encode the triplets of digits in 10 bits
    for i in range(num_triplets):
        encoded_int = int(msg[3 * i : 3 * i + 3])
        result.extend(int_to_bool_list(encoded_int, 10))

    # Encode the remaining digits
    # A single digit is encoded in 4 bits
    if num_remaining == 1:
        encoded_int = int(msg[-1])
        result.extend(int_to_bool_list(encoded_int, 4))
    # A pair of digits is encoded in 7 bits
    elif num_remaining == 2:
        encoded_int = int(msg[-2:])
        result.extend(int_to_bool_list(encoded_int, 7))

    return result


def _qr_encode_alphanumeric(msg: str) -> list[bool]:
    """Encode a string in alphanumeric mode"""
    result: list[bool] = []

    # Number of complete 2-character blocks
    num_pairs = len(msg) // 2
    num_remaining = len(msg) % 2

    # Encode the pairs of characters in 11 bits
    for i in range(num_pairs):
        encoded_int = 45 * alphanum_code(msg[2 * i]) + alphanum_code(msg[2 * i + 1])
        result.extend(int_to_bool_list(encoded_int, 11))

    # Encode the remaining character, if any, in 6 bits
    if num_remaining == 1:
        encoded_int = alphanum_code(msg[-1])
        result.extend(int_to_bool_list(encoded_int, 6))

    return result


# Function to convert a character to a number in the alphanumeric mode
def alphanum_code(char: str) -> int:
    """Converts a character to its corresponding alphanumeric code specified by
    the QR code specification.
    """
    if len(char) != 1:
        raise ValueError(f"Expected a single character, but got {char}!")

    try:
        return _ALPHANUM_CODES[char]
    except KeyError:
        logger.error(
            f"The character {char} cannot be encoded in the alphanumeric mode!"
        )
        raise ValueError(f" {char} cannot be encoded in the alphanumeric mode")


# Function to pad the message. Note that since the array is initialized to False,
# padding with zeros is equivalent to simply moving the index
def pad_data(data: list[bool], max_len: int) -> None:
    """Pad the data to the specified maximum length."""

    # The QR code specification requires alternative padding by the 8-bit
    # codewords 236 and 17.
    _PADDING = [int_to_bool_list(236, 8), int_to_bool_list(17, 8)]

    ind = len(data)
    pad_len = max_len - ind
    data.extend([False] * pad_len)

    # If only up to four bits are left, then we are done
    if pad_len <= 4:
        return

    # Add the terminator string of 4 zeros
    ind += 4

    # If the data length after this padding is not a multiple of 8,
    # move ahead until it is.
    rem = ind % 8
    if rem != 0:
        ind += 8 - rem

    # Alternatively pad with the two fixed boolean arrays stored in the constant PADDING
    # Pad with PADDING[0] if pflag is true and with PADDING[1] otherwise
    pflag = True
    while ind < max_len:
        if pflag:
            data[ind : ind + 8] = _PADDING[0]
        else:
            data[ind : ind + 8] = _PADDING[1]
        pflag = not pflag
        ind += 8
