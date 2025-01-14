# QR code generator

This repository contains a simple implementation of the model-2 [QR-code standard](https://en.wikipedia.org/wiki/QR_code) inspired by a recent [video](https://www.youtube.com/watch?v=w5ebcowAJD8) by [Veritasium](https://www.youtube.com/@veritasium). An example script to generate a QR-code corresponding to a given text string is provided in `example.py`.


## Usage 
The module provides a class `QRcode`, which can be imported as 
```
from QRcode import QRcode
```
An object of this class can be created by providing a version number (between 1 and 41), a data type (0,1,2 corresponding to numeric, alphanumeric, and binary) and a error-correction level (L, M, Q, or H) as 
```
qrobj = QRcode(version, datatype, ec_level) 
```
The QR code corresponding to a text string `msg` is then generated as 
```
qrobj.encode(msg) 
```
Finally, the QR code can be displayed using `qrcode.display()`, while various details of the generated QR code can be printed using `qrobj.print_stats()`.  


## Dependencies 
This package uses the following python packages: 

  - `numpy` for various numerical computations
  - `PIL` for converting the QR-code matrix into an image
  - `matlibplot.pyplot` for displaying the QR-code 
