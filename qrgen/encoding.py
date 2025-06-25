import logging

from .specification import QRspec, compute_msglen_bits
from .utils import int_to_bool, binary_to_int


logger = logging.getLogger(__name__)


# Standard boolean strings to pad the data (as defined in the QR code specification)
_PADDING = [
    list(map(bool, [1, 1, 1, 0, 1, 1, 0, 0])),  # 236 in binary
    list(map(bool, [0, 0, 0, 1, 0, 0, 0, 1])),  # 17 in binary
]

# # Standard boolean strings to pad the data (as defined in the QR code specification)
# PADDING = [
#     [1, 1, 1, 0, 1, 1, 0, 0],  # 236 in binary
#     [0, 0, 0, 1, 0, 0, 0, 1],  # 17 in binary
# ]


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


def create_header(msg: str, version: int, mode: int) -> list[bool]:
    """Creates the header for the QR code data."""
    datatype_code = [False] * 4
    datatype_code[-mode - 1] = True

    # Encode the message length
    num_msglen_bits = compute_msglen_bits(version, mode)
    msglen_encoded = int_to_bool(len(msg), num_msglen_bits)

    return datatype_code + msglen_encoded


def encode_msg(msg: str, mode: int) -> list[bool]:
    """Encode a string in the specified QR code encoding mode.

    Args:
        msg (str): The message to encode.
        mode (int): The encoding mode (0 for numeric, 1 for alphanumeric, 2 for binary).

    Returns:
        list[bool]: The encoded message as a list of boolean values."""
    match mode:
        case 0:
            logger.debug("Numerical encoding...")
            return _qr_encode_numeric(msg)
        case 1:
            logger.info("Converting to uppercase for alphanumeric encoding...")
            return _qr_encode_alphanumeric(msg.upper())
        case 2:
            logger.debug("Binary encoding...")
            return _qr_encode_binary(msg)
        case _:
            raise ValueError(f"{mode} is not a valid encoding mode; only 0-2 expected!")


def _qr_encode_binary(msg: str) -> list[bool]:
    """Encode a string in binary mode"""
    result: list[bool] = []
    for char in msg:
        result.extend(int_to_bool(ord(char), 8))

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
        result.extend(int_to_bool(encoded_int, 10))

    # Encode the remaining digits
    # A single digit is encoded in 4 bits
    if num_remaining == 1:
        encoded_int = int(msg[-1])
        result.extend(int_to_bool(encoded_int, 4))
    # A pair of digits is encoded in 7 bits
    elif num_remaining == 2:
        encoded_int = int(msg[-2:])
        result.extend(int_to_bool(encoded_int, 7))

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
        result.extend(int_to_bool(encoded_int, 11))

    # Encode the remaining character, if any, in 6 bits
    if num_remaining == 1:
        encoded_int = alphanum_code(msg[-1])
        result.extend(int_to_bool(encoded_int, 6))

    return result


# Function to convert a character to a number in the alphanumeric mode
def alphanum_code(char: str) -> int:
    """Converts a character to its corresponding alphanumeric code specified by
    the QR code specification.
    """

    if len(char) != 1:
        raise ValueError(f"Expected a single character, but got {char}!")

    if "0" <= char <= "9":  # Digits 0-9
        return ord(char) - 48
    elif "A" <= char <= "Z":  # (Uppercase) letters A-Z
        return ord(char) - 55
    elif char in _ALPHANUM_SYMBOL_CODES:  # Special characters
        return _ALPHANUM_SYMBOL_CODES[char]
    else:
        raise ValueError(
            f"The character {char} cannot be encoded in the alphanumeric mode!"
        )


# Function to pad the message. Note that since the array is initialized to False,
# padding with zeros is equivalent to simply moving the index
def pad_data(data: list[bool], max_len: int) -> None:
    """Pad the data to the specified maximum length."""

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


# Function to generate the data string (including error correction bits) for the QR-code
# This is the main function of the class that should be called after initialization
def encode(spec: QRspec, msg: str, dtype: int) -> list[int]:
    """Encodes the message in the specified QR code specification and data type.

    Args:
        spec (QRspec): The QR code specification.
        msg (str): The message to encode.
        dtype (int): The data type (0 for numeric, 1 for alphanumeric, 2 for binary).

    Returns:
        list[int]: The encoded message as a list of integers.
    """
    spec.validate()
    header = create_header(msg, spec.version, dtype)
    encoded_msg = encode_msg(msg, dtype)
    data = header + encoded_msg
    pad_data(data, spec.datalen_in_bits)

    return [binary_to_int(data[i : i + 8]) for i in range(0, len(data), 8)]
