import logging

# Path to the file containing the data specifications for the QR code
_DATASPEC_FILE = "qrgen/dataspec.txt"


logger = logging.getLogger(__name__)


class QRspec:
    """Class to hold the specifications for a QR code."""

    def __init__(
        self,
        version: int,
        EC_level: int,
        datalen: int,
        EC_bytes_per_block: int,
        num_blocks: list[int],
        datalen_per_block: list[int],
    ):
        self._version = version
        self._EC_level = EC_level
        self._datalen = datalen  # In bytes/modules
        self._EC_bytes_per_block = EC_bytes_per_block
        self._num_blocks = num_blocks
        self._datalen_per_block = datalen_per_block

        # Check if the specification is valid and raise suitable exceptions if not
        try:
            self.validate()
        except ValueError as e:
            raise ValueError(f"Error parsing spec obtained from {_DATASPEC_FILE}") from e

    def __repr__(self) -> str:
        return (
            f"QRspec(version={self._version}, EC_level={self._EC_level}, "
            f"data_bytes={self._datalen}, EC_bytes_per_block={self._EC_bytes_per_block}, "
            f"num_blocks={self._num_blocks}, data_bytes_per_block={self._datalen_per_block})"
        )

    def validate(self) -> None:
        """Checks if the QR code specification is valid."""
        if self._version < 1:
            raise ValueError(
                f"Invalid QR code version {self._version}. Version must be an integer between 1 and 40."
            )

    @property
    def version(self) -> int:
        """Returns the version of the QR code."""
        return self._version

    @property
    def EC_level(self) -> int:
        """Returns the version of the QR code."""
        return self._EC_level

    @property
    def EC_bytes_per_block(self) -> int:
        """Returns the version of the QR code."""
        return self._EC_bytes_per_block

    @property
    def datalen_in_bytes(self) -> int:
        """Returns the length of the data in bits."""
        return self._datalen

    @property
    def datalen_in_bits(self) -> int:
        """Returns the length of the data in bits."""
        return self.datalen_in_bytes * 8

    @property
    def num_blocks(self) -> list[int]:
        """Returns the number of blocks of each type in the QR code."""
        return self._num_blocks

    @property
    def datalen_per_block(self) -> list[int]:
        """Returns the length of the data in bytes for each block."""
        return self._datalen_per_block

    @property
    def block_list(self) -> list[int]:
        """Returns the list of block lengths of the QR code."""
        result = []
        for ind, num_blocks in enumerate(self._num_blocks):
            result.extend([self._datalen_per_block[ind]] * num_blocks)
        return result


def _parse_data_spec(line: str) -> QRspec:
    """
    Parses the data specification stored in the file with the given filename.
    Returns a dictionary with the version and error correction level as keys and the corresponding
    data specification as values.

    The format of the data specification file is as follows:
        The first two integers in each line are the version and error correction level.
        The third integer denotes the maximum allowed number of message bytes.
        The fourth integer is the number of error correction bytes per block.
        The next two integets are the number of blocks of type 1 and the number of message bytes per block.
        The next two integers are the corresponding quantities for blocks of type 2 (if applicable)
    """

    param_list = line.strip().split()
    if len(param_list) not in {6, 8}:
        raise ValueError(f"Found invalid data specification line: {line.strip()}.")

    try:
        param_list = [int(x) for x in param_list]
    except ValueError:
        raise ValueError(
            f"Invalid data specification line: {line.strip()}. All parameters must be integers."
        )

    version, EC_level, data_bytes, EC_bytes_per_block = param_list[:4]
    if len(param_list) == 6:
        num_blocks = [param_list[4]]
        data_bytes_per_block = [param_list[5]]
    else:
        num_blocks = [param_list[4], param_list[6]]
        data_bytes_per_block = [param_list[5], param_list[7]]

    return QRspec(
        version,
        EC_level,
        data_bytes,
        EC_bytes_per_block,
        num_blocks,
        data_bytes_per_block,
    )


def lookup_data_spec(filename: str):
    dataspec = {}
    with open(filename, "r") as file:
        for line in file:
            try:
                spec = _parse_data_spec(line)
            except ValueError:
                logger.warning(f"Skipping invalid line in {filename}: {line.strip()}")
                continue
            dataspec[(spec.version, spec.EC_level)] = spec
    return dataspec


def _compute_encoded_len(msglen: int, enc: int) -> int:
    """Computes the number of bits needed to encode the message length."""
    
    match enc:
        case 0:  # Numeric encoding
            msg_bits = 10 * (msglen // 3)
            if msglen % 2 == 1:
                msg_bits += 4  # One extra digit
            elif msglen % 3 == 2:
                msg_bits += 7
        case 1:  # Alphanumeric encoding
            msg_bits = 11 * (msglen // 2) + 6 * (msglen % 2)
        case 2:  # Binary encoding
            msg_bits = msglen * 8
        case 3:  # Kanji encoding (not implemented)
            raise NotImplementedError("Kanji encoding not implemented!")
        case _:
            raise ValueError(f"{enc} is not a valid data type; only 0-3 expected!")

    return msg_bits


def compute_msglen_bits(version: int, dtype: int) -> int:
    """Computes the number of bits needed to encode the message length."""
    match dtype:
        case 0:  # Numeric encoding
            if version <= 9:
                return 10
            elif version <= 26:
                return 12
            else:
                return 14
        case 1:  # Alphanumeric encoding
            if version <= 9:
                return 9
            elif version <= 26:
                return 11
            else:
                return 13
        case 2:  # Binary encoding
            if version <= 9:
                return 8
            else:
                return 16
        case 3:  # Kanji encoding (not implemented)
            raise NotImplementedError("Kanji encoding not implemented!")
        case _:
            raise ValueError(f"{dtype} is not a valid data type; only 0-3 expected!")


def _get_optimal_version(datalen: int, EC_level: int) -> int:
    """Returns the optimal version for the given data length and error correction level."""
    for version in range(1, MAX_VERSION+1):
        if (version, EC_level) in QR_SPEC_DICT:
            spec = QR_SPEC_DICT[(version, EC_level)]
            if spec.datalen_in_bits >= datalen:
                return version
    raise ValueError(
        f"Cannot find a suitable QR code version for encoding {datalen} bits with error correction level {EC_level}."
    )


def _get_optimal_EC_level(datalen: int, version: int) -> int:
    """Returns the optimal error correction level for a given data length and version."""
    for EC_level in [2,3,0,1]: # Check in order of decreasing error correction level
        if (version, EC_level) in QR_SPEC_DICT:
            spec = QR_SPEC_DICT[(version, EC_level)]
            if spec.datalen_in_bits >= datalen:
                return EC_level
    raise ValueError(
        f"Cannot find a suitable error correction level for encoding {datalen} bits with version {version}."
    )


def get_optimal_spec(msglen: int, version:int|None, EC_level: int|None, enc: int) -> QRspec:
    """Returns the optimal spec and the corresponding QRspec for the given message length."""
    max_header_len = 16
    encoded_msg_len = _compute_encoded_len(msglen, enc)
    max_datalen = encoded_msg_len + max_header_len

    if version is None:
        if EC_level is None:
            EC_level = 3  # Default to Q
        version = _get_optimal_version(max_datalen, _get_optimal_version(max_datalen, EC_level))
        return QR_SPEC_DICT[(version, EC_level)]
    
    elif 1 <= version <= MAX_VERSION:
        if EC_level is None:
            EC_level = _get_optimal_EC_level(max_datalen, version)
            return QR_SPEC_DICT[(version, EC_level)]    
        else:
            spec = QR_SPEC_DICT[(version, EC_level)]
            if spec.datalen_in_bits >= max_datalen:
                return spec
            else:
                raise ValueError(
                    f"QR code specification for version {version} and error correction level {EC_level} "
                    f"cannot accommodate a message of length {msglen} with data type {enc}."
                )



QR_SPEC_DICT = lookup_data_spec(_DATASPEC_FILE)
MAX_VERSION = max(QR_SPEC_DICT.keys(), key=lambda x: x[0])[0]
