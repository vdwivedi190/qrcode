from QRcode import QRcode 

# Message to be encoded
msg = "https://github.com/vdwivedi190/qrcode"

qrobj = QRcode(msg)
# We can alternatively initialize the QR-code object with the version, datatype, and error correction level
# qrobj = QRcode(msg, version=3, dtype=2, errcode='M')

# Display the QR-code 
# qrobj.display()

# Export the QR-code as an image file 
qrobj.export("qrcode.png")

# Print the details of the QR-code
qrobj.print_stats()