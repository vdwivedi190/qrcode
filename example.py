from QRcode import QRcode 

#  Initialize the QR-code parameters 
version = 2
datatype = 2           # Datatypes: 0=Numeric, 1=Alphanumeric, 2=Binary
err_level = 'M'       # Error correction level (L, M, Q, H)

# Message to be encoded
msg = "http://www.google.com"

#  Initialize the QR-code object 
qrobj = QRcode(version, datatype, err_level)

# Encode the message
qrobj.encode(msg) 

# Print the details of the QR-code
qrobj.print_stats()

# Display the QR-code
qrobj.display()