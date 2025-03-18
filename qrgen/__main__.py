import argparse 

from .QRcode import QRcode
from .terminal import print_to_terminal


def init_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qrgen", 
        description="Generates a QR Code for the given input message.",
        usage="python -m %(prog)s [OPTIONS] message"
    )

    parser.add_argument("message")
    parser.add_argument("--ver", metavar="VERSION", type=int, 
        help="QR version to encode with (between 1 and 40, chosen automatically if not provided)"
    )
    parser.add_argument("--enc", metavar="ENCODING", type=int, default=2, 
        help="Data type to encode the given string with (0/1/2 for numeric/alphanumeric/binary, default = binary)"
    )
    parser.add_argument("--ecl", metavar="EC_LEVEL", type=str, default='M', 
        help="Error correction level (L/M/Q/H, default=M)"
    )
    parser.add_argument("--out", metavar="FILENAME", 
        help="Output image file (default extension = png)"
    )
    parser.add_argument('-d', action='store_true', 
                        help="Display the QR-code on the screen"
    )
    parser.add_argument('-t', action='store_true', 
                        help="Display the QR-code on the terminal (ASCII art)"
    )
    parser.add_argument('-v', action='store_true', 
                        help="Print various statistics associated with the QR code"
    )

    return parser 


def export_qrcode(qrobj:QRcode, fname:str) -> None:
    try:
        qrobj.export(fname)
        print("Exported the QR code to", fname)
    except Exception as e:
        print("Encountered a problem exporting the QR code: " + str(e))
        raise SystemExit
    

def display_stats(stats):
    print("QR Code:")
    print(f"  Version = {stats['version']}")
    print(f"  Encoding = {stats['encoding']}")
    print(f"  Error Correction Level = {stats['ec_level']}")
    print()
    print(f"  Size of the QR-code = {stats['qr_size']} x {stats['qr_size']} = {stats['qr_size']**2} modules")
    print(f"  Number of preset modules = {stats['num_func_mods']}")
    print(f"  Number of data modules = {stats['num_data_mods']}")
    print(f"  Encoded using pattern mask number {stats['masknum']}")
    print()
    print(f"  Message Length = {stats['message_length']}")
    print(f"  Total number of data codewords = {stats['num_data_words']}")
    print(f"  Number of message codewords = {stats['num_msg_words']}")
    print(f"  Number of error correction codewords = {stats['num_data_words']-stats['num_msg_words']}")


def main() -> None:
    parser = init_parser()
    args = parser.parse_args()

    try:
        qrobj = QRcode(args.message, version=args.ver, dtype=args.enc, errcode=args.ecl)
        qrobj.generate()
    except Exception as e:
        print("Error creating QR code: " + str(e))
        raise SystemExit

    if args.out:
        export_qrcode(qrobj, args.out)
        
    if args.d:
        try:
            qrobj.display()
        except Exception as e:
            print("Error displaying the QR code: " + str(e))

    if args.t:
        print_to_terminal(qrobj.qrmat)
    
    if args.v:
        stats = qrobj.get_stats() 
        display_stats(stats)


main() 
  