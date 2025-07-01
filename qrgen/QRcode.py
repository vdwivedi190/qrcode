import logging

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

from .QRmatrix import QRmatrix
from .spec import QRspec, get_spec
from .encoding import encode
from .interlacing import split_data_in_blocks, interlace_blocks, bits_from_blocks
from .error_correction import compute_EC_blocks

logger = logging.getLogger(__name__)


class QRcode:
    """Class for generating QR codes.

    This class takes a string and generates a QR code based on the following parameters
    (which are passed as keyword arguments to the constructor):
        - `version`: an integer between 1 and 40 (both inclusive)
        - `error_correction_level`: 'L', 'M', 'Q', or 'H' (default = 'Q')
        - `encoding`: 'numeric', 'alphanumeric', or 'binary' (default = binary).
    If a version is not provided, the smallest version that can encode the message with
    the specified error correction level and encoding will be chosen automatically.

    The constructor raises a TypeError or ValueError if the provided parameters are invalid.
    The 'KANJI' encoding is not implemented and raises a NotImplementedError.

    The QR code is generated only when it is needed by one of the public methods, which includes
    'display()', 'export()', 'get_image()', and 'get_stats()`. See the corresponding docstrings for
    more details on each method. Once generated, the QR code is stored and is not regenerated for
    the subsequent calls to the public methods. The (re)generation of the QR code can be forced at
    any time by calling the `generate()` method.
    """

    def __init__(
        self,
        msg: str = "",
        *,
        version: int | None = None,
        error_correction_level: str = "Q",
        encoding: str = "binary",
    ):
        if version is not None and not isinstance(version, int):
            raise TypeError(f" integer expected for version, instead got '{version}'")

        if not isinstance(encoding, str):
            raise TypeError(
                f" string ('numeric', 'alphanumeric', or 'binary') expected for encoding, instead got '{encoding}'"
            )

        if not isinstance(error_correction_level, str):
            raise TypeError(
                f" string ('L', 'M', 'Q', or 'H') expected for error correction level, instead got '{error_correction_level}'"
            )

        logging.info("Input data types valid. Initializing QRcode object.")
        self.msg = str(msg)
        try:
            self._spec: QRspec = get_spec(
                len(msg), version, error_correction_level, encoding
            )
        except ValueError as err:
            logging.exception(err)
            raise

    def generate(self) -> None:
        """Generates the QR code based on the provided message and specifications."""

        logging.info(f"Encoding the data in {self._spec.encoding.name.lower()} mode.")
        data = encode(spec=self._spec, msg=self.msg)

        logging.info("Adding error correction bits.")
        data_blocks = split_data_in_blocks(self._spec, data)
        EC_blocks = compute_EC_blocks(self._spec.EC_bytes_per_block, data_blocks)
        all_blocks = interlace_blocks(self._spec, data_blocks, EC_blocks)
        bitstring = bits_from_blocks(all_blocks)
        logging.info("Encoded data generated successfully.")

        logging.info("Adding the data to the QR code matrix.")
        self.qr_obj = QRmatrix(self._spec)
        self.qr_obj.add_data(bitstring)
        self.qr_obj.pattern_mask()
        self.qrmat = self.qr_obj.mat

        logging.info("Generating image from the QR-code matrix.")
        self._create_image()

    def __str__(self):
        if not hasattr(self, "qrmat"):
            return "QR code not generated"
        return "Encoded message = " + self.msg

    def _create_image(self) -> None:
        """Creates a PIL Image object from the QR code matrix."""
        padding = 6
        self.tmp_img = Image.fromarray(np.uint8(~self.qrmat) * 255)
        width, height = self.tmp_img.size

        # The mode 'L' is for a 8-bit grayscale image
        logging.info(f"Padding image with {padding} modules on each side.")

        self.qrimg = Image.new(
            mode="L", size=(width + 2 * padding, height + 2 * padding), color=255
        )
        self.qrimg.paste(self.tmp_img, (padding, padding))

    def get_image(self) -> Image:
        """Returns the QR code as a PIL Image object."""
        if not hasattr(self, "qrimg"):
            self.generate()

        return self.qrimg

    def display(self):
        """Displays the QR code using matplotlib."""
        if not hasattr(self, "qrimg"):
            self.generate()

        fig, ax = plt.subplots(1, 1, figsize=(14, 6))
        ax.axis("off")
        fig.subplots_adjust(left=0.25, right=0.75, top=0.75, bottom=0.25)
        ax.imshow(self.qrimg, cmap="gray", vmin=0, vmax=255)
        plt.show()

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
        stats["version"] = self._spec.version
        stats["encoding"] = self._spec.encoding.name
        stats["error_correction_level"] = self._spec.error_correction_level.name
        stats["qr_size"] = self.qr_obj.size

        stats["capacity"] = self._spec.capacity_in_bytes
        stats["num_data_words"] = self._spec.datalen_in_bytes
        stats["num_error_correction_words"] = (
            self._spec.capacity_in_bytes - self._spec.datalen_in_bytes
        )

        stats["message"] = self.msg
        stats["message_length"] = len(self.msg)
        stats["pattern_mask_number"] = self.qr_obj.masknum

        return stats
