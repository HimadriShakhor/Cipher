#!/usr/bin/env python3
"""
binary_tool.py — Binary encoder / decoder
Run in Windows CMD: python binary_tool.py
"""

import argparse, sys

def encode_text(text: str) -> str:
    """Convert plain text to 8-bit binary (space-separated)."""
    return " ".join(format(ord(ch), "08b") for ch in text)

def decode_binary(binary: str) -> str:
    """Convert binary string (space-separated or continuous) back to text."""
    # Normalize input: split by whitespace
    bits = binary.strip().split()
    out_chars = []
    for b in bits:
        try:
            out_chars.append(chr(int(b, 2)))
        except Exception:
            out_chars.append("?")
    return "".join(out_chars)

# ---------------- Interactive ----------------
def interactive():
    print("Binary Encoder / Decoder")
    print("========================")
    print("Options:")
    print("  1) Encode text -> Binary")
    print("  2) Decode Binary -> Text")
    print("  3) Encode a text file -> binary file")
    print("  4) Decode a binary file -> text file")
    print("  5) Quit")

    while True:
        choice = input("\nChoose option (1-5): ").strip()
        if choice == "1":
            txt = input("Enter text: ")
            print("Binary:", encode_text(txt))
        elif choice == "2":
            b = input("Enter binary (8-bit, space separated): ")
            print("Decoded:", decode_binary(b))
        elif choice == "3":
            infile = input("Input text file: ")
            outfile = input("Output binary file: ")
            try:
                with open(infile, "r", encoding="utf-8") as f:
                    data = f.read()
                binary = encode_text(data)
                with open(outfile, "w", encoding="utf-8") as f:
                    f.write(binary)
                print(f"Saved binary to {outfile}")
            except Exception as e:
                print("Error:", e)
        elif choice == "4":
            infile = input("Input binary file: ")
            outfile = input("Output text file: ")
            try:
                with open(infile, "r", encoding="utf-8") as f:
                    data = f.read()
                text = decode_binary(data)
                with open(outfile, "w", encoding="utf-8") as f:
                    f.write(text)
                print(f"Saved decoded text to {outfile}")
            except Exception as e:
                print("Error:", e)
        elif choice == "5":
            print("Bye.")
            break
        else:
            print("Invalid option.")

# ---------------- CLI ----------------
def main_cli():
    parser = argparse.ArgumentParser(description="Binary encoder/decoder")
    parser.add_argument("-e", "--encode", metavar='"TEXT"', help="Encode TEXT to binary")
    parser.add_argument("-d", "--decode", metavar='"BINARY"', help="Decode BINARY to text")
    parser.add_argument("--infile", "-i", help="Input file")
    parser.add_argument("--outfile", "-o", help="Output file")
    args = parser.parse_args()

    if len(sys.argv) == 1:
        interactive()
        return

    if args.encode:
        result = encode_text(args.encode)
    elif args.decode:
        result = decode_binary(args.decode)
    elif args.infile and args.outfile:
        try:
            with open(args.infile, "r", encoding="utf-8") as f:
                data = f.read()
            if args.encode is not None:
                result = encode_text(data)
            else:
                result = decode_binary(data)
            with open(args.outfile, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"Output saved to {args.outfile}")
            return
        except Exception as e:
            print("Error:", e)
            return
    else:
        parser.print_help()
        return

    if args.outfile:
        with open(args.outfile, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"Output saved to {args.outfile}")
    else:
        print(result)

if __name__ == "__main__":
    main_cli()
