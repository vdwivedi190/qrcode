import logging

import argparse

from .terminal import print_to_terminal

try:
    from .QRcode import QRcode
except ImportError:
    print("Could not import the QR code package: Spec file missing!!! ")
    raise SystemExit


def init_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qrgen",
        description="Generates a QR Code for the given input message.",
        usage="python -m %(prog)s [OPTIONS] message",
    )

    parser.add_argument("message")
    parser.add_argument(
        "--ver",
        metavar="VERSION",
        type=int,
        help="QR version to encode with (between 1 and 40, chosen automatically if not provided)",
    )
    parser.add_argument(
        "--enc",
        metavar="ENCODING",
        type=str,
        default="binary",
        help="Encoding (numeric/alphanumeric/binary, default = binary)",
    )
    parser.add_argument(
        "--ecl",
        metavar="EC_LEVEL",
        type=str,
        default="M",
        help="Error correction level (L/M/Q/H, default=Q)",
    )
    parser.add_argument(
        "--out", metavar="FILENAME", help="Output image file (default extension = png)"
    )
    parser.add_argument(
        "-d", action="store_true", help="Display the QR-code on the screen"
    )
    parser.add_argument(
        "-t",
        action="store_true",
        help="Display the QR-code on the terminal (ASCII art)",
    )
    parser.add_argument(
        "-v",
        action="store_true",
        help="Print various statistics associated with the QR code",
    )

    return parser


def export_qrcode(qrobj: QRcode, fname: str) -> None:
    try:
        qrobj.export(fname)
        print("Exported the QR code to", fname)
    except Exception as e:
        print("Encountered a problem exporting the QR code: " + str(e))
        raise SystemExit


def display_stats(stats):
    print("QR Code:")
    print(f"  Version = {stats['version']}")
    print(f"  Encoding = {stats['encoding'].lower()}")
    print(f"  Error Correction Level = {stats['error_correction_level']}")
    print(f"  Encoded using pattern mask number {stats['pattern_mask_number']}")
    print()

    print(
        f"  Size of the QR-code = {stats['qr_size']} x {stats['qr_size']} = {stats['qr_size'] ** 2} modules"
    )
    print(f"  Maximum number of codewords = {stats['capacity']}")
    print(f"  Number of data codewords = {stats['num_data_words']}")
    print(
        f"  Number of error correction codewords = {stats['num_error_correction_words']}"
    )
    print()

    print(f"  Encoded Message = {stats['message']}")

    print(f"  Message Length = {stats['message_length']} characters")


def main() -> None:
    logging.basicConfig(
        format="{asctime}: {levelname} - {name} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename="./qrcode.log",
        filemode="w",  # Overwrite the log file each time
        level=logging.INFO,
    )

    parser = init_parser()
    args = parser.parse_args()

    try:
        qrobj = QRcode(
            args.message,
            version=args.ver,
            encoding=args.enc,
            error_correction_level=args.ecl,
        )
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
