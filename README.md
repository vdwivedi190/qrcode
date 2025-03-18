# QR code generator

This repository contains a simple implementation of the model-2 [QR-code standard](https://en.wikipedia.org/wiki/QR_code).  An example script to generate a QR-code corresponding to a given text string is provided in `example.py`, running which should output a png file with a QR-code linking to this page:

## Description
A QR-code is described by the following three parameters: 

  - **Version**: This is an integer between 1 and 40 that determines the number of bits (called "modules") in the QR-code. A version $v$ QR-code is a $N \times N$ rectangle with $N = 4v+17$.
  - **Encoding**: The format of the data encoded in QR-code is indicated by an integer between 0 and 3, corresponding to a numerical string (0), and alphanumeric string (1), a binary string (2), or a _Kanji_ string (3). This implementation only supports encodings 0-2. 
  - **Error correction level**: The fraction of QR-code devoted to error correction is controlled by the error-correction level (L, M, Q, or H), with L being the lowest level and H the highest. 


## Usage 
The module can be used either by importing it or invoked directly from the terminal. 

### Importing the module 
The module provides a class `QRcode`, which can be imported as 
```
from QRcode import QRcode
```
An object of this class can be created most simply by providing a message string as 
```
msg = "Hello World!"
qrobj = QRcode(msg) 
```
This chooses a suitable version and encodes `msg` as a binary string with error correction level M. The version, encoding and error correction level can instead be provided explicitly as 
```
qrobj = QRcode(msg, version=3, dtype=2, errcode='Q')
```
The relevant methods associated with this object are:

  - `QRcode.get_image()`: Returns the QR-code as a PIL `Image` object.
  - `QRcode.export(filename:str) -> None`: Exports the QR-code to the image file. If the file extension is unrecognized, then the image is saved in the PNG format and a ValueError is raised.
  - `QRcode.display()`: Displays the QR-code using `pyplot`
  - `QRcode.get_stats()`: Returns a dictionary with various parameters associated with the generated QR-code
  - `QRcode.generate()`: Generates the QR-code. This function is automatically called by the functions above and the resulting QR-code matrix and image cached.
      
Note that the generation of the QR code is lazy, i.e., the QR code is not generated until it is required. A `ValueError` is raised by `QRcode.generate()` if the message is too long to be encoded by a QR-code of a given version, or if the message contains characters incompatible with the desired encoding, such as non-numeric characters if `dtype=0` (numeric mode) is specified. 

### Running from the terminal
The module can be directly invoked from the terminal as `python -m qrgen ...`. The various allowed options are 

```
vatsal@qrcode>python -m qrgen --help
usage: python -m qrgen [OPTIONS] message

Generates a QR Code for the given input message.

positional arguments:
  message

options:
  -h, --help      show this help message and exit
  --ver VERSION   QR version to encode with (between 1 and 40, chosen automatically if not provided)
  --enc ENCODING  Data type to encode the given string with (0/1/2 for numeric/alphanumeric/binary, default = binary)
  --ecl EC_LEVEL  Error correction level (L/M/Q/H, default=Q)
  --out FILENAME  Output image file (default extension = png)
  -d              Display the QR-code on the screen
  -t              Display the QR-code on the terminal (ASCII art)
  -v              Print various statistics associated with the QR code
```

For instance, a QR-code directing to this page can be generated as 
```
vatsal@qrcode>python -m qrgen --out="test.png" 'https://github.com/vdwivedi190/qrcode'
```
whose output is the following image:

<img src="./qrcode.png" alt="QR code" width="400">


## Dependencies 
This package uses the following python packages: 

  - `numpy` for various numerical computations
  - `PIL` for converting the QR-code matrix into an image
  - `matlibplot.pyplot` for displaying the QR-code

## References/Acknowledgements

  - A basic introduction to QR-codes and the inspiration for this project is the recent [video](https://www.youtube.com/watch?v=w5ebcowAJD8) by [Veritasium](https://www.youtube.com/@veritasium).
  - A detailed description of the QR-code standard can be found [here](https://www.thonky.com/qr-code-tutorial)
