#!/usr/bin/env python3
"""
morse_tool.py — Morse code encoder / decoder with audible beeps (Windows only)
Run in CMD: python morse_tool.py
"""

import argparse, sys, time

# Windows-only sound
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

# Morse dictionary
MORSE_CODE_DICT = {
    'A': '.-',    'B': '-...',  'C': '-.-.',  'D': '-..',
    'E': '.',     'F': '..-.',  'G': '--.',   'H': '....',
    'I': '..',    'J': '.---',  'K': '-.-',   'L': '.-..',
    'M': '--',    'N': '-.',    'O': '---',   'P': '.--.',
    'Q': '--.-',  'R': '.-.',   'S': '...',   'T': '-',
    'U': '..-',   'V': '...-',  'W': '.--',   'X': '-..-',
    'Y': '-.--',  'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--',
    '4': '....-', '5': '.....', '6': '-....', '7': '--...',
    '8': '---..', '9': '----.',
    ' ': '/'
}

# Reverse dict for decoding
REVERSE_MORSE_CODE_DICT = {v: k for k, v in MORSE_CODE_DICT.items()}

# Sound settings
FREQ = 800
DOT = 100   # ms
DASH = 300  # ms
GAP_SYMBOL = 0.1   # seconds
GAP_LETTER = 0.3   # seconds
GAP_WORD = 0.7     # seconds

# ---------------- Core functions ----------------
def encode_text(text: str) -> str:
    return " ".join(MORSE_CODE_DICT.get(ch, "") for ch in text.upper())

def decode_morse(morse: str) -> str:
    words = morse.split(" / ")
    decoded_words = []
    for word in words:
        letters = word.split()
        decoded_letters = [REVERSE_MORSE_CODE_DICT.get(l, "?") for l in letters]
        decoded_words.append("".join(decoded_letters))
    return " ".join(decoded_words)

def play_morse(morse: str):
    """Play Morse as beeps."""
    if not HAS_WINSOUND:
        print("winsound not available (Windows only).")
        return
    for symbol in morse:
        if symbol == ".":
            winsound.Beep(FREQ, DOT)
            time.sleep(GAP_SYMBOL)
        elif symbol == "-":
            winsound.Beep(FREQ, DASH)
            time.sleep(GAP_SYMBOL)
        elif symbol == " ":
            time.sleep(GAP_LETTER)
        elif symbol == "/":
            time.sleep(GAP_WORD)

# ---------------- Interactive ----------------
def interactive():
    print("Morse Code Encoder / Decoder with Beeps")
    print("=======================================")
    print("Options:")
    print("  1) Encode text -> Morse")
    print("  2) Decode Morse -> Text")
    print("  3) Encode text -> Play Morse beeps")
    print("  4) Quit")

    while True:
        choice = input("\nChoose option (1-4): ").strip()
        if choice == "1":
            txt = input("Enter text: ")
            print("Morse:", encode_text(txt))
        elif choice == "2":
            m = input("Enter Morse (use / for space): ")
            print("Decoded:", decode_morse(m))
        elif choice == "3":
            txt = input("Enter text: ")
            morse = encode_text(txt)
            print("Morse:", morse)
            play_morse(morse)
        elif choice == "4":
            print("Bye.")
            break
        else:
            print("Invalid option.")

# ---------------- CLI ----------------
def main_cli():
    parser = argparse.ArgumentParser(description="Morse encoder/decoder with optional sound")
    parser.add_argument("-e", "--encode", metavar='"TEXT"', help="Encode TEXT to Morse")
    parser.add_argument("-d", "--decode", metavar='"MORSE"', help="Decode MORSE to Text")
    parser.add_argument("--beep", action="store_true", help="Play Morse audio when encoding")
    args = parser.parse_args()

    if len(sys.argv) == 1:
        interactive()
        return

    if args.encode:
        result = encode_text(args.encode)
        print(result)
        if args.beep:
            play_morse(result)
    elif args.decode:
        result = decode_morse(args.decode)
        print(result)
    else:
        parser.print_help()

if __name__ == "__main__":
    main_cli()
