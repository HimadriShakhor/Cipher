#!/usr/bin/env python3
"""
enigma_tool.py — Enigma machine simulator
Run in Windows CMD: python enigma_tool.py
"""

import argparse, sys

# ---------------- Rotor/Reflector wirings ----------------
ROTOR_WIRINGS = {
    "I":     "EKMFLGDQVZNTOWYHXUSPAIBRCJ",
    "II":    "AJDKSIRUXBLHWTMCQGZNPYFVOE",
    "III":   "BDFHJLCPRTXVZNYEIWGAKMUSQO",
    "IV":    "ESOVPZJAYQUIRHXLNFTGKDCMWB",
    "V":     "VZBRGITYUPSDNHLXAWMJQOFECK"
}
ROTOR_NOTCHES = {
    "I":     "Q",
    "II":    "E",
    "III":   "V",
    "IV":    "J",
    "V":     "Z"
}
REFLECTORS = {
    "A": "EJMZALYXVBWFCRQUONTSPIKHGD",
    "B": "YRUHQSLDPXNGOKMIEBFZCWVJAT",
    "C": "FVPJIAOYEDRZXWGCTKUQSBNMHL"
}

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# ---------------- Enigma Components ----------------
class Rotor:
    def __init__(self, wiring: str, notch: str, position: str = "A", ring_setting: int = 0):
        self.wiring = wiring
        self.notch = notch
        self.position = ALPHABET.index(position)
        self.ring_setting = ring_setting  # 0–25

    def enc_forward(self, c: int) -> int:
        shift = (c + self.position - self.ring_setting) % 26
        encoded = ALPHABET.index(self.wiring[shift])
        return (encoded - self.position + self.ring_setting) % 26

    def enc_backward(self, c: int) -> int:
        shift = (c + self.position - self.ring_setting) % 26
        encoded = self.wiring.index(ALPHABET[shift])
        return (encoded - self.position + self.ring_setting) % 26

    def step(self) -> bool:
        self.position = (self.position + 1) % 26
        return ALPHABET[self.position] == self.notch

class Reflector:
    def __init__(self, wiring: str):
        self.wiring = wiring

    def reflect(self, c: int) -> int:
        return ALPHABET.index(self.wiring[c])

class Plugboard:
    def __init__(self, pairs: str = ""):
        self.mapping = {ch: ch for ch in ALPHABET}
        for pair in pairs.upper().split():
            if len(pair) == 2:
                a, b = pair[0], pair[1]
                self.mapping[a], self.mapping[b] = b, a

    def swap(self, c: str) -> str:
        return self.mapping.get(c, c)

# ---------------- Enigma Machine ----------------
class EnigmaMachine:
    def __init__(self, rotors, reflector, plugboard_pairs=""):
        self.rotors = rotors
        self.reflector = reflector
        self.plugboard = Plugboard(plugboard_pairs)

    def encode_letter(self, c: str) -> str:
        if c not in ALPHABET:
            return c

        # Step rotors (right rotor always steps)
        rotate_next = self.rotors[-1].step()
        # Double-stepping mechanism
        if rotate_next:
            rotate_next = self.rotors[-2].step()
            if rotate_next:
                self.rotors[-3].step()

        # Pass through plugboard
        c = self.plugboard.swap(c)
        idx = ALPHABET.index(c)

        # Forward through rotors
        for r in reversed(self.rotors):
            idx = r.enc_forward(idx)

        # Reflect
        idx = self.reflector.reflect(idx)

        # Backward through rotors
        for r in self.rotors:
            idx = r.enc_backward(idx)

        # Back through plugboard
        c = ALPHABET[idx]
        return self.plugboard.swap(c)

    def encode_message(self, text: str) -> str:
        out = []
        for ch in text.upper():
            if ch in ALPHABET:
                out.append(self.encode_letter(ch))
            else:
                out.append(ch)
        return "".join(out)

# ---------------- CLI & Interactive ----------------
def interactive():
    print("Enigma Machine Simulator")
    print("========================")
    print("Default config: Rotors I-II-III (AAA), Reflector B, no plugboard")

    while True:
        msg = input("\nEnter message (blank to quit): ").strip()
        if not msg:
            print("Bye.")
            break

        # Reset machine each time (like setting daily key)
        r1 = Rotor(ROTOR_WIRINGS["I"], ROTOR_NOTCHES["I"], "A")
        r2 = Rotor(ROTOR_WIRINGS["II"], ROTOR_NOTCHES["II"], "A")
        r3 = Rotor(ROTOR_WIRINGS["III"], ROTOR_NOTCHES["III"], "A")
        ref = Reflector(REFLECTORS["B"])
        machine = EnigmaMachine([r1, r2, r3], ref)

        encoded = machine.encode_message(msg)
        print("Encoded/Decoded:", encoded)

def main_cli():
    parser = argparse.ArgumentParser(description="Enigma machine simulator")
    parser.add_argument("-e", "--encode", metavar='"TEXT"', help="Encode/Decode text")
    parser.add_argument("--rotors", default="I II III", help="Rotor sequence (default: I II III)")
    parser.add_argument("--positions", default="AAA", help="Starting positions (default: AAA)")
    parser.add_argument("--reflector", default="B", help="Reflector type (A, B, or C)")
    parser.add_argument("--plugboard", default="", help="Plugboard pairs (e.g. 'AB CD EF')")
    args = parser.parse_args()

    if len(sys.argv) == 1:
        interactive()
        return

    rotor_names = args.rotors.split()
    if len(rotor_names) != 3:
        print("Must provide 3 rotors.")
        return
    positions = args.positions.upper()
    if len(positions) != 3:
        print("Positions must be 3 letters.")
        return

    rotors = []
    for name, pos in zip(rotor_names, positions):
        rotors.append(Rotor(ROTOR_WIRINGS[name], ROTOR_NOTCHES[name], pos))

    reflector = Reflector(REFLECTORS[args.reflector.upper()])
    machine = EnigmaMachine(rotors, reflector, args.plugboard)

    result = machine.encode_message(args.encode)
    print(result)

if __name__ == "__main__":
    main_cli()
