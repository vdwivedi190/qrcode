import logging
from enum import IntEnum, unique

from .dataspec import DataSpec, spec_dict_from_file
from .error_correction import compute_error_correction_bits
from .utils import int_to_bool_list, str_to_bool_list

logger = logging.getLogger(__name__)

# Sizes of the corner and alignment blocks
CORNER_SIZE = 7
ALIGNMENT_BLOCKSIZE = 5

# Boolean arrays for computing the error correction bits
# These are used to compute the error correction bits for the version and format information.
# The polynomials are defined in the QR code standard.
VERSION_POLYNOMIAL: list[bool] = str_to_bool_list("1111100100101")
FORMAT_POLYNOMIAL: list[bool] = str_to_bool_list("10100110111")
FORMAT_MASK: list[bool] = str_to_bool_list("101010000010010")


@unique
class Encoding(IntEnum):
    """Enum for the different types of encoding used in QR codes."""

    NUMERIC = 0
    ALPHANUMERIC = 1
    BINARY = 2
    KANJI = 3

    def get_code(self) -> list[bool]:
        """Returns the encoding code as a list of boolean values."""
        code = [False] * 4
        code[-self.value - 1] = True
        return code


@unique
class ErrorCorrectionLevel(IntEnum):
    """Enum for the different error correction levels used in QR codes."""

    L = 1
    M = 0
    Q = 3
    H = 2


class QRspec:
    """Class to hold the specifications for a QR code."""

    def __init__(
        self,
        version: int,
        EC_level: ErrorCorrectionLevel,
        encoding: Encoding,
        dataspec: DataSpec,
    ):
        self._version = version
        self._EC_level = EC_level
        self._encoding = encoding
        self._dataspec = dataspec

    def __repr__(self) -> str:
        return (
            f"QRspec(version={self._version}, EC_level={self._EC_level}, "
            f"data_bytes={self._dataspec.datalen}, EC_bytes_per_block={self._dataspec.EC_bytes_per_block}, "
            f"num_blocks={self._dataspec.num_blocks}, data_bytes_per_block={self._dataspec.datalen_per_block})"
        )

    @property
    def version(self) -> int:
        """Returns the version of the QR code."""
        return self._version

    @property
    def error_correction_level(self) -> ErrorCorrectionLevel:
        """Returns the version of the QR code."""
        return self._EC_level

    @property
    def encoding(self) -> Encoding:
        """Returns the encoding type of the QR code."""
        return self._encoding

    @property
    def EC_bytes_per_block(self) -> int:
        """Returns the version of the QR code."""
        return self._dataspec.EC_bytes_per_block

    @property
    def datalen_in_bytes(self) -> int:
        """Returns the length of the data in bits."""
        return self._dataspec.datalen

    @property
    def datalen_in_bits(self) -> int:
        """Returns the length of the data in bits."""
        return self.datalen_in_bytes * 8

    @property
    def capacity_in_bytes(self) -> int:
        """Returns the total capacity of the QR code in bytes."""
        return self._dataspec.datalen + self._dataspec.EC_bytes_per_block * sum(
            self._dataspec.num_blocks
        )

    @property
    def num_blocks(self) -> list[int]:
        """Returns the number of blocks of each type in the QR code."""
        return self._dataspec.num_blocks

    @property
    def datalen_per_block(self) -> list[int]:
        """Returns the length of the data in bytes for each block."""
        return self._dataspec.datalen_per_block

    @property
    def block_list(self) -> list[int]:
        """Returns the list of block lengths of the QR code."""
        result = []
        for ind, num_blocks in enumerate(self._dataspec.num_blocks):
            result.extend([self._dataspec.datalen_per_block[ind]] * num_blocks)
        return result

    @property
    def num_msglen_bits(self) -> int:
        match self._encoding:
            case Encoding.NUMERIC:
                if self._version <= 9:
                    return 10
                elif self._version <= 26:
                    return 12
                else:
                    return 14
            case Encoding.ALPHANUMERIC:
                if self._version <= 9:
                    return 9
                elif self._version <= 26:
                    return 11
                else:
                    return 13
            case Encoding.BINARY:
                if self._version <= 9:
                    return 8
                else:
                    return 16
            case Encoding.KANJI:
                raise NotImplementedError("Kanji encoding not implemented!")

    def version_to_bool_array(self, encoding_len: int = CORNER_SIZE - 1) -> list[bool]:
        """Returns a boolean array encoding the version with error correction bits."""
        result = int_to_bool_list(self._version, encoding_len)
        result += compute_error_correction_bits(result, VERSION_POLYNOMIAL)
        return result

    def format_to_bool_array(self, mask_num: int) -> list[bool]:
        """Returns a boolean array encoding the error correction level and pattern mask."""
        EC_list = int_to_bool_list(self._EC_level.value, 2)
        masknum_list = int_to_bool_list(mask_num, 3)
        result = EC_list + masknum_list
        result += compute_error_correction_bits(result, FORMAT_POLYNOMIAL)
        for ind, bit in enumerate(FORMAT_MASK):
            result[ind] ^= bit
        return result


def _compute_encoded_len(msglen: int, encoding: Encoding) -> int:
    """Compute the number of bits needed to encode a message of length msglen with a given encoding."""

    match encoding:
        case Encoding.NUMERIC:
            msg_bits = 10 * (msglen // 3)
            if msglen % 3 == 1:  # One extra digit
                msg_bits += 4
            elif msglen % 3 == 2:  # Two extra digits
                msg_bits += 7
        case Encoding.ALPHANUMERIC:
            msg_bits = 11 * (msglen // 2) + 6 * (msglen % 2)
        case Encoding.BINARY:
            msg_bits = msglen * 8
        case Encoding.KANJI:
            raise NotImplementedError("Kanji encoding not implemented!")

    return msg_bits


# def _get_optimal_version(datalen: int, EC_level: int, spec_dict:dict[tuple[int,int], DataSpec]) -> int:
#     """Returns the optimal version for the given data length and error correction level."""
#     for version in range(1, MAX_VERSION + 1):
#         if (version, EC_level) in spec_dict:
#             if spec_dict[(version, EC_level)].datalen_in_bits >= datalen:
#                 return version
#     raise ValueError(
#         f" cannot encode {datalen} bits with error correction level {EC_level} for any version."
#     )


def get_spec(
    message_len: int, version: int | None, EC_level: str, encoding: str
) -> QRspec:
    """Returns the QR code specification for the given message length, version, error correction level, and encoding type."""

    try:
        spec_dict: dict[tuple[int, int], DataSpec] = spec_dict_from_file()
    except FileNotFoundError as err:
        logger.exception(err)
        raise OSError(" error loading the QR code specifications ") from err

    max_version = max(spec_dict.keys(), key=lambda x: x[0])[0]

    # Get the Encoding enum from the provided encoding string
    try:
        encoding_ = Encoding[encoding.upper()]
    except KeyError:
        raise ValueError(
            f" invalid encoding type {encoding}. Expected one of ({list(Encoding.__members__.keys())})"
        )

    # Get the ErrorCorrectionLevel enum from the provided error correction level string
    try:
        EC_level_ = ErrorCorrectionLevel[EC_level.upper()]
    except KeyError:
        raise ValueError(
            f" invalid error correction level {EC_level}. Expected one of ({list(Encoding.__members__.keys())})"
        )

    # Compute the maximum number of bits needed to encode the message,
    # (Note that this does not include the error correction bits.)
    max_header_len = 16
    encoded_message_len = _compute_encoded_len(message_len, encoding_)
    max_datalen = encoded_message_len + max_header_len

    if version is None:
        logger.warning(
            "No version provided. The smallest suitable version will be used."
        )

        for version in range(1, max_version + 1):
            if (version, EC_level_) in spec_dict:
                dataspec_ = spec_dict[(version, EC_level_)]
                if dataspec_.datalen_in_bits >= max_datalen:
                    version_ = version
                    logger.info(f"Using version {version_} to encode the message. ")
                    break
        else:
            # If no suitable version is found, try with the lowest error correction level and the highest version
            logger.warning(
                f"Cannot encode the message at error correction level {EC_level_}."
                "Trying to encode with the lowest error correction level (L)."
            )
            dataspec_ = spec_dict[(max_version, ErrorCorrectionLevel.L)]
            if dataspec_.datalen_in_bits >= max_datalen:
                version_ = max_version
                logger.info(f"Using version {version_} to encode the message. ")
            else:
                raise ValueError(" cannot encode the message for any version1.")
    elif 1 <= version <= max_version:
        version_ = version
        dataspec_ = spec_dict[(version_, EC_level_)]
        if dataspec_.datalen_in_bits < max_datalen:
            raise ValueError(
                f" QR code version {version_} with error correction level {EC_level_.name} cannot accomodate "
                f" the message encoded in {encoding_.name} mode"
            )

    else:
        raise ValueError(
            f" invalid QR code version {version}. Version must be an integer between 1 and {max_version}."
        )

    logger.debug(
        f"Using {encoding_.name.lower()} encoding at version {version_} with error correction level {EC_level_.name} "
    )
    logger.debug(f"Data specification: {dataspec_}")
    return QRspec(
        version=version_,
        EC_level=EC_level_,
        encoding=encoding_,
        dataspec=dataspec_,
    )
