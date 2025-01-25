# QR code generator

This repository contains a simple implementation of the model-2 [QR-code standard](https://en.wikipedia.org/wiki/QR_code).  An example script to generate a QR-code corresponding to a given text string is provided in `example.py`, running which should output a png file with a QR-code linking to this page:
![QR-code to this page](./qrcode.png)

A QR-code is described by the following three parameters: 

  - **Version**: This is an integer between 1 and 40 that determines the number of bits (called "modules") in the QR-code. A version $v$ QR-code is a $NxN$ rectangle with $N = 4v+17$.
  - **Encoding**: The format of the data encoded in QR-code is indicated by an integer between 0 and 3, corresponding to a numerical string (0), and alphanumeric string (1), a binary string (2), or a _Kanji_ string (3). This implementation only supports encodings 0-2. 
  - **Error correction level**: The fraction of QR-code devoted to error correction is controlled by the error-correction level (L, M, Q, or H), with L being the lowest level and H the highest. 


## Usage 
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
The QR code so generated can either be displayed using `qrobj.display()` or exported to an image file using `qrobj.export(image_file.png)`. Finally, various details of the QR-code can be displayed using `qrobj.print_stats()`.  


## Dependencies 
This package uses the following python packages: 

  - `numpy` for various numerical computations
  - `PIL` for converting the QR-code matrix into an image
  - `matlibplot.pyplot` for displaying the QR-code 

## References/Acknowledgements

  - A basic introduction to QR-codes and the inspiration for this project is the recent [video](https://www.youtube.com/watch?v=w5ebcowAJD8) by [Veritasium](https://www.youtube.com/@veritasium).
  - A detailed description of the QR-code standard can be found [here](https://www.thonky.com/qr-code-tutorial)