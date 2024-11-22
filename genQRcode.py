# A basic file to generate QR code using the QRcode package

import QRcode as qr 

msg = input("Enter the message to encode:")
version = int(input("Enter QR code version: "))
errlvl = int(input("Enter error level (e.g., 1): "))
dtype = 2

qrmat, fmask, maxbits = qr.initialize(version)

qr.encode_data(qrmat, fmask, msg, dtype, version, errlvl, maxbits)
masknum = qr.pattern_mask(qrmat, version, errlvl, fmask)

qr.display(qrmat)
