import logging

# Configure logging here to ensure that it is set up before any other imports that might use logging
logging.basicConfig(
    format="{levelname} - {name} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="../qrcode.log",
    filemode="w",  # 'w' to overwrite the log file each time
    level=logging.DEBUG,
)

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

from .QRmatrix import QRmatrix
from .specification import QRspec, get_optimal_spec
from .encoding import encode
from .interlacing import split_data_in_blocks, interlace_blocks, bits_from_blocks
from .error_correction import compute_EC_blocks


logger = logging.getLogger(__name__)


class QRcode:
    """Class for generating QR codes."""

    DATATYPE_ID = {0: "Numeric", 1: "Alphanumeric", 2: "Binary"}
    MAX_CAPACITY = {0: 7089, 1: 4296, 2: 2953}

    EC_LEVEL_ID = {0: "M", 1: "L", 2: "H", 3: "Q"}
    EC_LEVEL_CODE = {"L": 1, "M": 0, "Q": 3, "H": 2}

    # Default encoding = binary
    # Default error correction level = M
    # If a version number is not provided, then it is computed based on the length of the message

    def __init__(
        self,
        msg: str = "",
        version: int | None = None,
        encoding: int = 2,
        errcode: str = "M",
    ):
        logging.info("Initializing QRcode object...")

        try:
            _validate_inputs(version, encoding, errcode)
        except (ValueError, TypeError, NotImplementedError) as e:
            logging.error(f"Invalid input: {e}")
            raise e

        self.msg = msg
        self.encoding = encoding
        EC_level = self.EC_LEVEL_CODE[errcode]
        self._spec: QRspec = get_optimal_spec(len(msg), version, EC_level, encoding)

    def generate(self) -> None:
        """Generates the QR code based on the provided message and specifications."""

        logging.info("Generating QR code.")
        data = encode(spec=self._spec, msg=self.msg, dtype=self.encoding)
        data_blocks = split_data_in_blocks(data, spec=self._spec)
        EC_blocks = compute_EC_blocks(self._spec, data_blocks)
        all_blocks = interlace_blocks(self._spec, data_blocks, EC_blocks)
        bitstring = bits_from_blocks(all_blocks)

        logging.info("Adding to a matrix.")
        self.qr_obj = QRmatrix(self._spec.version, self._spec.EC_level)
        self.qr_obj.add_data(bitstring)
        self.qr_obj.pattern_mask()
        self.qrmat = self.qr_obj.mat

        logging.info("Generating image from matrix.")
        self._create_image()

    def _create_image(self) -> None:
        # Generate the QR code image (with white padding)
        padding = 6
        self.tmp_img = Image.fromarray(np.uint8(~self.qrmat) * 255)
        width, height = self.tmp_img.size

        # The mode 'L' is for a 8-bit grayscale image
        logging.info(f"Padding image with {padding} modules on each side.")

        self.qrimg = Image.new(
            mode="L", size=(width + 2 * padding, height + 2 * padding), color=255
        )
        self.qrimg.paste(self.tmp_img, (padding, padding))

    # PRINTING ROUNTINES
    # =================================================================

    def __str__(self):
        if not hasattr(self, "qrmat"):
            return "QR code not generated"
        return "Encoded message = " + self.msg

    def display(self):
        """Displays the QR code using matplotlib."""
        if not hasattr(self, "qrimg"):
            self.generate()

        fig, ax = plt.subplots(1, 1, figsize=(14, 6))
        ax.axis("off")
        fig.subplots_adjust(left=0.25, right=0.75, top=0.75, bottom=0.25)
        ax.imshow(self.qrimg, cmap="gray", vmin=0, vmax=255)
        plt.show()

    def get_image(self) -> Image:
        """Returns the QR code as a PIL Image object."""
        if not hasattr(self, "qrimg"):
            self.generate()

        return self.qrimg

    def export(self, filename: str, scale: int = 20) -> None:
        """Exports the QR code to an image file."""
        if not hasattr(self, "qrimg"):
            self.generate()

        width, height = self.qrimg.size
        resized_img = self.qrimg.resize(
            (width * scale, height * scale), resample=Image.NEAREST
        )

        try:
            resized_img.save(filename)
        except ValueError:
            resized_img.save(filename, format="png")
            raise ValueError(
                "Could not determine format from extension; using PNG instead"
            )
        except OSError:
            raise Exception("Error saving the QR code as", filename)

    def get_stats(self) -> dict:
        """Returns a dictionary with statistics about the QR code."""
        if not hasattr(self, "qrmat"):
            self.generate()

        stats = {}
        stats["version"] = self.version
        stats["encoding"] = self.DATATYPE_ID[self.encoding]
        stats["ec_level"] = self.EC_LEVEL_ID[self.errlvl]
        stats["masknum"] = self.qr_obj.masknum

        stats["qr_size"] = self.qr_obj.size
        stats["num_func_mods"] = self.qr_obj.num_func_bits
        stats["num_data_mods"] = self.qr_obj.size**2 - self.qr_obj.num_func_bits
        stats["num_data_words"] = self.data_obj.num_databytes
        stats["num_msg_words"] = self.data_obj.num_msgbytes

        stats["message"] = self.msg
        stats["message_length"] = self.msglen

        return stats


def _validate_inputs(version, encoding, errcode):
    """Validates the inputs for the QR code generation.

    Raises ValueError, TypeError, or NotImplementedError if the inputs are invalid."""

    if version is not None and not isinstance(version, int):
        raise TypeError(f"{version} is not a valid version number; integer expected!")

    if not isinstance(encoding, int):
        raise TypeError(f"{encoding} is not a valid data type; integer expected!")
    elif encoding not in [0, 1, 2]:
        raise ValueError(f"{encoding} is not a valid data type; only 0-3 expected!")
    elif encoding == 3:
        raise NotImplementedError("Kanji mode (Data type 3) not supported!")

    if errcode is not None and errcode not in ["L", "M", "Q", "H"]:
        raise ValueError(
            f"{errcode} is not a valid error correction levels! Expected values are 'L', 'M', 'Q', or 'H'!"
        )
