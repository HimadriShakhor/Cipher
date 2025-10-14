#!/usr/bin/env python3
"""
morse_tool.py — Morse code encoder / decoder
Run in Windows CMD: python morse_tool.py
Or quick encode: python morse_tool.py -e "Hello World"
Decode from CLI: python morse_tool.py -d ".... . .-.. .-.. --- / .-- --- .-. .-.. -.."
"""

import argparse
import sys
from typing import Dict

MORSE: Dict[str, str] = {
    "A": ".-",    "B": "-...",  "C": "-.-.", "D": "-..",
    "E": ".",     "F": "..-.",  "G": "--.",  "H": "....",
    "I": "..",    "J": ".---",  "K": "-.-",  "L": ".-..",
    "M": "--",    "N": "-.",    "O": "---",  "P": ".--.",
    "Q": "--.-",  "R": ".-.",   "S": "...",  "T": "-",
    "U": "..-",   "V": "...-",  "W": ".--",  "X": "-..-",
    "Y": "-.--",  "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--",
    "4": "....-", "5": ".....", "6": "-....", "7": "--...",
    "8": "---..", "9": "----.",
    ".": ".-.-.-", ",": "--..--", "?": "..--..", "'": ".----.",
    "!": "-.-.--", "/": "-..-.",  "(": "-.--.",  ")": "-.--.-",
    "&": ".-...",  ":": "---...", ";": "-.-.-.", "=": "-...-",
    "+": ".-.-.",  "-": "-....-", "_": "..--.-", "\"": ".-..-.",
    "$": "...-..-","@": ".--.-.",
    " ": "/"   # we use '/' as word separator in morse text
}

# Reverse mapping
REVERSE_MORSE = {v: k for k, v in MORSE.items()}

LETTER_SEP = " "   # separator between letters in output Morse
WORD_SEP = " / "   # separator between words in output Morse


def encode_text(plain: str) -> str:
    """Encode plain text to Morse code. Words separated by ' / '. Letters by spaces."""
    out_parts = []
    for ch in plain.upper():
        if ch in MORSE:
            out_parts.append(MORSE[ch])
        else:
            # For unknown characters, preserve them in brackets to show they're unsupported
            out_parts.append("[?]")
    # join by space; ensure words use ' / ' for readability
    return " ".join(out_parts).replace(" / ", WORD_SEP.strip()).replace("/","/")  # ensure slash single


def decode_morse(morse: str) -> str:
    """Decode morse string to text.
    Accepts:
      - letters separated by spaces
      - words separated by '/' or ' / ' or multiple spaces
    """
    # Normalize separators: allow both '/' and ' / ' and triple spaces
    morse = morse.strip()
    # Replace multiple spaces with single space, but keep slashes as word markers
    # We'll split by ' / ' or '/' first into words
    words = [w.strip() for w in morse.replace(" / ", "/").split("/")]
    decoded_words = []
    for w in words:
        if not w:
            decoded_words.append("")
            continue
        letters = [s for s in w.split() if s != ""]
        decoded_letters = []
        for code in letters:
            ch = REVERSE_MORSE.get(code)
            if ch:
                decoded_letters.append(ch)
            else:
                # Unknown morse sequence -> place '?' so user sees an error
                decoded_letters.append("?")
        decoded_words.append("".join(decoded_letters))
    return " ".join(decoded_words)


def interactive():
    print("Morse Encoder / Decoder")
    print("========================")
    print("Options:")
    print("  1) Encode text -> Morse")
    print("  2) Decode Morse -> text")
    print("  3) Encode a text file -> morse file")
    print("  4) Decode a morse file -> text file")
    print("  5) Quit")
    while True:
        try:
            choice = input("\nChoose option (1-5): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            return
        if choice == "1":
            txt = input("Enter text to encode: ")
            print("\nMorse:")
            print(encode_text(txt))
        elif choice == "2":
            m = input("Enter morse to decode (use '/' for word gaps): ")
            print("\nDecoded:")
            print(decode_morse(m))
        elif choice == "3":
            infile = input("Path to input text file: ").strip()
            outfile = input("Path to output morse file: ").strip()
            try:
                with open(infile, "r", encoding="utf-8") as f:
                    data = f.read()
                morse = encode_text(data)
                with open(outfile, "w", encoding="utf-8") as f:
                    f.write(morse)
                print(f"Saved morse to {outfile}")
            except Exception as e:
                print("Error:", e)
        elif choice == "4":
            infile = input("Path to input morse file: ").strip()
            outfile = input("Path to output text file: ").strip()
            try:
                with open(infile, "r", encoding="utf-8") as f:
                    data = f.read()
                text = decode_morse(data)
                with open(outfile, "w", encoding="utf-8") as f:
                    f.write(text)
                print(f"Saved decoded text to {outfile}")
            except Exception as e:
                print("Error:", e)
        elif choice == "5":
            print("Bye.")
            return
        else:
            print("Invalid option. Enter 1-5.")


def main_cli():
    parser = argparse.ArgumentParser(description="Morse code encoder/decoder")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-e", "--encode", metavar='"TEXT"', help="Encode TEXT to Morse (quote if contains spaces).")
    group.add_argument("-d", "--decode", metavar='"MORSE"', help="Decode MORSE to text (use '/' for word gaps).")
    parser.add_argument("--infile", "-i", help="Read input from file (use with -e or -d).")
    parser.add_argument("--outfile", "-o", help="Write output to file.")
    args = parser.parse_args()

    # If no args, run interactive
    if len(sys.argv) == 1:
        interactive()
        return

    # file I/O path
    if args.infile:
        try:
            with open(args.infile, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print("Could not read infile:", e)
            sys.exit(1)
    else:
        content = args.encode if args.encode is not None else args.decode

    if args.encode is not None or (args.infile and args.encode is None and args.decode is None and args.infile):
        # encode mode triggered by -e OR by using infile with -e flag (but parser logic avoids ambiguous)
        if args.encode is None and args.infile and args.decode is None:
            # ambiguous: user provided infile only; default to encode
            mode = "encode"
        else:
            mode = "encode" if args.encode is not None else "decode"
    else:
        mode = "decode" if args.decode is not None else "encode"

    if mode == "encode":
        input_text = content
        result = encode_text(input_text)
    else:
        # mode == decode
        input_text = content
        result = decode_morse(input_text)

    if args.outfile:
        try:
            with open(args.outfile, "w", encoding="utf-8") as f:
                f.write(result)
            print(f"Output written to {args.outfile}")
        except Exception as e:
            print("Could not write outfile:", e)
            sys.exit(1)
    else:
        print(result)


if __name__ == "__main__":
    main_cli()
