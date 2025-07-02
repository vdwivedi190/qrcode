import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Path to the file containing the data specifications for the QR code
_DATASPEC_FILE = "qrgen/dataspec.txt"


@dataclass(frozen=True)
class DataSpec:
    """Data class to hold the various for a QR code."""

    datalen: int
    EC_bytes_per_block: int
    num_blocks: list[int]
    datalen_per_block: list[int]

    @property
    def datalen_in_bytes(self) -> int:
        """Returns the length of the data in bits."""
        return self.datalen

    @property
    def datalen_in_bits(self) -> int:
        """Returns the length of the data in bits."""
        return self.datalen_in_bytes * 8


def _parse_data_spec(line: str) -> tuple[int, int, DataSpec]:
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

    return (
        version,
        EC_level,
        DataSpec(
            data_bytes,
            EC_bytes_per_block,
            num_blocks,
            data_bytes_per_block,
        ),
    )


def spec_dict_from_file(
    filename: str = _DATASPEC_FILE,
) -> dict[tuple[int, int], DataSpec]:
    spec_dict = {}
    try:
        with open(filename, "r") as file:
            for line in file:
                try:
                    version, EC_level, dataspec = _parse_data_spec(line)
                except ValueError:
                    logger.info(f"Skipping invalid line in {filename}: {line.strip()}")
                    continue
                spec_dict[(version, EC_level)] = dataspec
    except FileNotFoundError as err:
        logger.critical(f"Data specification file {filename} not found.")
        raise OSError(f"Data specification file {filename} not found.") from err
    return spec_dict
