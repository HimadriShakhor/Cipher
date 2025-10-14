#!/usr/bin/env python3
"""
binary_tool.py — Binary encoder/decoder with beeps and sound input (Windows only for playback, cross-platform for listening)
Dependencies:
    pip install sounddevice numpy
"""

import argparse, sys, time
import numpy as np

# ---------------- Sound playback (Windows only) ----------------
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

# ---------------- Sound recording ----------------
try:
    import sounddevice as sd
    HAS_SD = True
except ImportError:
    HAS_SD = False

# Config
FREQ = 800       # Hz frequency for beeps
SHORT = 100      # duration for '0' in ms
LONG = 300       # duration for '1' in ms
GAP_BIT = 0.1    # gap between bits (s)
GAP_BYTE = 0.3   # gap between bytes (s)

# ---------------- Core binary functions ----------------
def encode_text(text: str) -> str:
    return " ".join(format(ord(ch), "08b") for ch in text)

def decode_binary(binary: str) -> str:
    bits = binary.strip().split()
    out_chars = []
    for b in bits:
        try:
            out_chars.append(chr(int(b, 2)))
        except Exception:
            out_chars.append("?")
    return "".join(out_chars)

def play_binary(binary: str):
    """Play binary as beeps."""
    if not HAS_WINSOUND:
        print("winsound not available (Windows only).")
        return
    bits = binary.strip().split()
    for b in bits:
        for bit in b:
            if bit == "0":
                winsound.Beep(FREQ, SHORT)
            elif bit == "1":
                winsound.Beep(FREQ, LONG)
            time.sleep(GAP_BIT)
        time.sleep(GAP_BYTE)

# ---------------- Record and decode beeps ----------------
def listen_binary(duration=5, samplerate=44100, threshold=0.2):
    """
    Record audio and try to detect binary beeps.
    Only works reliably in a quiet environment.
    """
    if not HAS_SD:
        print("sounddevice not installed. Run: pip install sounddevice numpy")
        return ""

    print(f"Listening for {duration} seconds... (make your beeps now)")
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='float32')
    sd.wait()

    # Convert to numpy array
    audio = np.squeeze(audio)

    # Detect amplitude envelope
    energy = np.abs(audio)
    energy = (energy > threshold).astype(int)

    # Segment into chunks (approx SHORT=0.1s, LONG=0.3s)
    samples_per_short = int(samplerate * 0.1)
    bits = []
    i = 0
    while i < len(energy):
        if energy[i] == 1:  # beep detected
            length = 0
            while i < len(energy) and energy[i] == 1:
                length += 1
                i += 1
            # decide 0 vs 1 by length
            duration_s = length / samplerate
            if duration_s < 0.2:
                bits.append("0")
            else:
                bits.append("1")
        else:
            i += 1

    # Group into bytes (8 bits per char)
    binary = ""
    if bits:
        for j in range(0, len(bits), 8):
            binary += "".join(bits[j:j+8]) + " "
    return binary.strip()

# ---------------- Interactive menu ----------------
def interactive():
    print("Binary Encoder / Decoder with Beeps + Listener")
    print("==============================================")
    print("Options:")
    print("  1) Encode text -> Binary")
    print("  2) Decode Binary -> Text")
    print("  3) Encode a text file -> binary file")
    print("  4) Decode a binary file -> text file")
    print("  5) Encode text -> Play Binary as beeps")
    print("  6) Listen & decode binary from sound")
    print("  7) Quit")

    while True:
        choice = input("\nChoose option (1-7): ").strip()
        if choice == "1":
            txt = input("Enter text: ")
            print("Binary:", encode_text(txt))
        elif choice == "2":
            b = input("Enter binary: ")
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
            txt = input("Enter text: ")
            binary = encode_text(txt)
            print("Binary:", binary)
            play_binary(binary)
        elif choice == "6":
            binary = listen_binary()
            if binary:
                print("Heard binary:", binary)
                print("Decoded:", decode_binary(binary))
            else:
                print("No binary detected.")
        elif choice == "7":
            print("Bye.")
            break
        else:
            print("Invalid option.")

# ---------------- CLI ----------------
def main_cli():
    parser = argparse.ArgumentParser(description="Binary encoder/decoder with sound")
    parser.add_argument("-e", "--encode", metavar='"TEXT"', help="Encode TEXT to binary")
    parser.add_argument("-d", "--decode", metavar='"BINARY"', help="Decode BINARY to text")
    parser.add_argument("--beep", action="store_true", help="Play Binary audio when encoding")
    parser.add_argument("--listen", action="store_true", help="Listen and decode binary from sound")
    args = parser.parse_args()

    if len(sys.argv) == 1:
        interactive()
        return

    if args.encode:
        result = encode_text(args.encode)
        print(result)
        if args.beep:
            play_binary(result)
    elif args.decode:
        result = decode_binary(args.decode)
        print(result)
    elif args.listen:
        binary = listen_binary()
        if binary:
            print("Heard binary:", binary)
            print("Decoded:", decode_binary(binary))
        else:
            print("No binary detected.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main_cli()
