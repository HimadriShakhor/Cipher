#!/usr/bin/env python3
"""
hybrid_cipher_fixed.py — Fixed Hybrid cipher tool (AES-GCM + optional XOR + optional Enigma)
Usage examples:
  - Interactive: python hybrid_cipher_fixed.py
  - Encrypt CLI: python hybrid_cipher_fixed.py -e -p "mypassword" -m "hello world" --xor
  - Decrypt CLI: python hybrid_cipher_fixed.py -d -p "mypassword" -m "<packaged-string>"

Requires: cryptography
Install: pip install cryptography
"""

import argparse, sys, os, base64, json, secrets, hashlib
from typing import Tuple

# --- cryptography imports ---
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except Exception:
    AESGCM = None

# ---------------- Enigma (simple 3-rotor version) ----------------
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ROTOR_WIRINGS = {
    "I": "EKMFLGDQVZNTOWYHXUSPAIBRCJ",
    "II": "AJDKSIRUXBLHWTMCQGZNPYFVOE",
    "III": "BDFHJLCPRTXVZNYEIWGAKMUSQO"
}
ROTOR_NOTCHES = {"I":"Q","II":"E","III":"V"}
REFLECTOR_B = "YRUHQSLDPXNGOKMIEBFZCWVJAT"

class Rotor:
    def __init__(self, wiring, notch, pos="A", ring=0):
        self.wiring = wiring
        self.notch = notch
        self.pos = ALPHABET.index(pos)
        self.ring = ring
    def enc_f(self, c):
        shift = (c + self.pos - self.ring) % 26
        encoded = ALPHABET.index(self.wiring[shift])
        return (encoded - self.pos + self.ring) % 26
    def enc_b(self, c):
        shift = (c + self.pos - self.ring) % 26
        encoded = self.wiring.index(ALPHABET[shift])
        return (encoded - self.pos + self.ring) % 26
    def step(self):
        self.pos = (self.pos + 1) % 26
        return ALPHABET[self.pos] == self.notch

class Enigma:
    def __init__(self, rotor_names=("I","II","III"), positions="AAA", plugboard_pairs=""):
        # rotor_names: iterable of rotor name strings length exactly equal to positions length
        rotor_names_list = list(rotor_names)
        if len(rotor_names_list) != len(positions):
            # if mismatch, try to align first N
            rotor_names_list = rotor_names_list[:len(positions)]
        self.rotors = [Rotor(ROTOR_WIRINGS[n], ROTOR_NOTCHES[n], p) for n,p in zip(rotor_names_list, positions)]
        self.reflector = REFLECTOR_B
        # plugboard mapping
        self.plug = {c:c for c in ALPHABET}
        for pair in (plugboard_pairs or "").upper().split():
            if len(pair) == 2:
                a,b = pair[0], pair[1]
                if a in ALPHABET and b in ALPHABET:
                    self.plug[a], self.plug[b] = b,a
    def _swap(self, ch): return self.plug.get(ch,ch)
    def _reflect(self, i): return ALPHABET.index(self.reflector[i])
    def process_char(self, ch):
        if ch not in ALPHABET: return ch
        # step rightmost rotor every keypress
        rotate = self.rotors[-1].step()
        # double-step behaviour (approximation)
        if rotate and len(self.rotors) > 1:
            rotate2 = self.rotors[-2].step()
            if rotate2 and len(self.rotors) > 2:
                self.rotors[-3].step()
        c = self._swap(ch)
        idx = ALPHABET.index(c)
        # forward (right -> left)
        for r in reversed(self.rotors):
            idx = r.enc_f(idx)
        # reflect
        idx = self._reflect(idx)
        # backward (left -> right)
        for r in self.rotors:
            idx = r.enc_b(idx)
        out = ALPHABET[idx]
        return self._swap(out)
    def process_text(self, text):
        out = []
        for ch in text.upper():
            out.append(self.process_char(ch))
        return "".join(out)

# ---------------- Crypto helpers ----------------
def derive_key(password: str, salt: bytes, iterations: int = 200_000, key_len: int = 32) -> bytes:
    """Derive a key from password and salt using PBKDF2-HMAC-SHA256."""
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=key_len)

def xor_bytes(data: bytes, password: str, salt: bytes) -> bytes:
    """Derive keystream from password+salt and XOR with data."""
    # use PBKDF2 to generate a stream of bytes at least as long as data
    # If data is long, we generate same length stream
    stream = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000, dklen=len(data))
    return bytes(a ^ b for a, b in zip(data, stream))

def aes_gcm_encrypt(key: bytes, plaintext: bytes) -> Tuple[bytes, bytes]:
    """Return (nonce, ciphertext_with_tag). AESGCM produces ciphertext||tag."""
    if AESGCM is None:
        raise RuntimeError("cryptography library not installed. Install with: pip install cryptography")
    aes = AESGCM(key)
    nonce = secrets.token_bytes(12)
    ct = aes.encrypt(nonce, plaintext, associated_data=None)
    return nonce, ct

def aes_gcm_decrypt(key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
    if AESGCM is None:
        raise RuntimeError("cryptography library not installed. Install with: pip install cryptography")
    aes = AESGCM(key)
    return aes.decrypt(nonce, ciphertext, associated_data=None)

# ---------------- High-level encrypt/decrypt ----------------
def encrypt(password: str, plaintext: bytes, use_xor: bool=False, use_enigma: bool=False, enigma_cfg=None) -> str:
    """
    Returns string: json(header) + '.' + base64(salt|nonce|ciphertext)
    header includes flags and enigma_cfg when used.
    """
    salt = secrets.token_bytes(16)
    work_plain = plaintext

    # ensure cfg is dict
    enigma_cfg = dict(enigma_cfg or {})

    # optional enigma
    if use_enigma:
        rotors = tuple(enigma_cfg.get("rotors", ("I","II","III")))
        pos = enigma_cfg.get("positions", "AAA")
        plug = enigma_cfg.get("plugboard", "")
        en = Enigma(rotors, pos, plug)
        # operate on text; non-letters pass unchanged
        try:
            text_in = work_plain.decode("utf-8")
        except Exception:
            raise ValueError("Enigma layer requires UTF-8 text input (no binary).")
        work_plain = en.process_text(text_in).encode("utf-8")

    # optional XOR obfuscation before AES
    if use_xor:
        work_plain = xor_bytes(work_plain, password, salt)

    # derive AES key and encrypt with AES-GCM
    key = derive_key(password, salt)
    nonce, ciphertext = aes_gcm_encrypt(key, work_plain)

    blob = salt + nonce + ciphertext
    b64 = base64.b64encode(blob).decode("utf-8")

    header = {"xor": bool(use_xor), "enigma": bool(use_enigma)}
    # include enigma_cfg in header so decrypt can reconstruct it
    if use_enigma:
        # ensure serializable forms
        header["enigma_cfg"] = {
            "rotors": list(enigma_cfg.get("rotors", ("I","II","III"))),
            "positions": enigma_cfg.get("positions", "AAA"),
            "plugboard": enigma_cfg.get("plugboard", "")
        }

    return json.dumps(header) + "." + b64

def decrypt(password: str, packaged: str) -> bytes:
    """
    packaged format: json_header + '.' + base64blob
    blob = salt(16) | nonce(12) | ciphertext
    """
    if "." not in packaged:
        raise ValueError("Packaged format missing separator (header.payload).")

    try:
        header_s, b64 = packaged.split(".", 1)
        header = json.loads(header_s)
    except Exception:
        raise ValueError("Invalid packaged format (header JSON error).")

    blob = base64.b64decode(b64.encode("utf-8"))
    if len(blob) < 16 + 12 + 16:  # minimal heuristic (salt + nonce + tag)
        raise ValueError("Packaged blob too short / corrupted.")

    salt = blob[:16]
    nonce = blob[16:28]
    ciphertext = blob[28:]
    key = derive_key(password, salt)
    plaintext = aes_gcm_decrypt(key, nonce, ciphertext)

    # reverse XOR if present
    if header.get("xor"):
        plaintext = xor_bytes(plaintext, password, salt)

    # reverse enigma if present (enigma is symmetric)
    if header.get("enigma"):
        cfg = header.get("enigma_cfg", {})
        rotors = tuple(cfg.get("rotors", ("I","II","III")))
        positions = cfg.get("positions", "AAA")
        plug = cfg.get("plugboard", "")
        en = Enigma(rotors, positions, plug)
        # plaintext must be text for Enigma operation
        try:
            s = plaintext.decode("utf-8")
        except Exception:
            raise ValueError("Decrypted data isn't valid UTF-8 text, cannot apply Enigma reverse.")
        plaintext = en.process_text(s).encode("utf-8")

    return plaintext

# ---------------- CLI / Interactive ----------------
def interactive():
    print("Hybrid Cipher Tool (AES-GCM + optional XOR + optional Enigma) - FIXED")
    print("-------------------------------------------------------------------")
    while True:
        print("\nOptions:\n 1) Encrypt text\n 2) Decrypt packaged\n 3) Encrypt file\n 4) Decrypt file\n 5) Quit")
        choice = input("Choose (1-5): ").strip()
        if choice == "1":
            pwd = input("Password: ").strip()
            txt = input("Plaintext: ")
            xor = input("Use XOR obfuscation before AES? (y/N): ").lower().startswith("y")
            en = input("Use Enigma layer before XOR? (y/N): ").lower().startswith("y")
            enigma_cfg = {}
            if en:
                rotnames = input("Rotor names (space-separated, default 'I II III'): ") or "I II III"
                pos = input("Positions (3 letters, default 'AAA'): ") or "AAA"
                plug = input("Plugboard pairs (e.g. 'AB CD', default ''): ") or ""
                enigma_cfg = {"rotors": tuple(rotnames.split()), "positions": pos, "plugboard": plug}
            packaged = encrypt(pwd, txt.encode("utf-8"), use_xor=xor, use_enigma=en, enigma_cfg=enigma_cfg)
            print("\nPackaged output (copy exactly):\n")
            print(packaged)
        elif choice == "2":
            pwd = input("Password: ").strip()
            packaged = input("Packaged input (paste): ").strip()
            try:
                out = decrypt(pwd, packaged)
                print("\nPlaintext:\n")
                print(out.decode("utf-8", errors="replace"))
            except Exception as e:
                print("Decryption failed:", e)
        elif choice == "3":
            pwd = input("Password: ").strip()
            infile = input("Input file path: ").strip()
            outfile = input("Output file path (will contain packaged): ").strip()
            xor = input("Use XOR? (y/N): ").lower().startswith("y")
            en = input("Use Enigma? (y/N): ").lower().startswith("y")
            enigma_cfg = {}
            if en:
                rotnames = input("Rotor names (default 'I II III'): ") or "I II III"
                pos = input("Positions (default 'AAA'): ") or "AAA"
                plug = input("Plugboard pairs: ") or ""
                enigma_cfg = {"rotors": tuple(rotnames.split()), "positions": pos, "plugboard": plug}
            with open(infile, "rb") as f:
                data = f.read()
            packaged = encrypt(pwd, data, use_xor=xor, use_enigma=en, enigma_cfg=enigma_cfg)
            with open(outfile, "w", encoding="utf-8") as f:
                f.write(packaged)
            print("Saved packaged data to", outfile)
        elif choice == "4":
            pwd = input("Password: ").strip()
            infile = input("Input packaged file path: ").strip()
            outfile = input("Output file path for plaintext: ").strip()
            with open(infile, "r", encoding="utf-8") as f:
                packaged = f.read().strip()
            try:
                data = decrypt(pwd, packaged)
                with open(outfile, "wb") as f:
                    f.write(data)
                print("Decrypted saved to", outfile)
            except Exception as e:
                print("Decryption failed:", e)
        elif choice == "5":
            print("Bye.")
            break
        else:
            print("Invalid choice.")

def main_cli():
    parser = argparse.ArgumentParser(description="Hybrid cipher (AES-GCM + optional XOR + optional Enigma)")
    parser.add_argument("-e", "--encrypt", action="store_true", help="Encrypt message")
    parser.add_argument("-d", "--decrypt", action="store_true", help="Decrypt packaged message")
    parser.add_argument("-p", "--password", help="Password")
    parser.add_argument("-m", "--message", help="Message (plaintext for encrypt or packaged for decrypt)")
    parser.add_argument("--xor", action="store_true", help="Use XOR obfuscation")
    parser.add_argument("--enigma", action="store_true", help="Use Enigma layer (before XOR and AES)")
    parser.add_argument("--infile", help="Input file")
    parser.add_argument("--outfile", help="Output file")
    args = parser.parse_args()

    if len(sys.argv) == 1:
        interactive()
        return

    if args.encrypt:
        if AESGCM is None:
            print("ERROR: cryptography package not found. Install with: pip install cryptography")
            return
        if not args.password:
            print("Password required (-p)")
            return
        enigma_cfg = {}
        if args.enigma:
            # CLI mode doesn't accept complex enigma cfg; use defaults or env variables if needed
            enigma_cfg = {"rotors": ("I","II","III"), "positions": "AAA", "plugboard": ""}
        if args.infile:
            with open(args.infile, "rb") as f:
                data = f.read()
            packaged = encrypt(args.password, data, use_xor=args.xor, use_enigma=args.enigma, enigma_cfg=enigma_cfg)
            if args.outfile:
                with open(args.outfile, "w", encoding="utf-8") as f:
                    f.write(packaged)
                print("Saved packaged to", args.outfile)
            else:
                print(packaged)
        else:
            if not args.message:
                print("Provide message with -m")
                return
            packaged = encrypt(args.password, args.message.encode("utf-8"), use_xor=args.xor, use_enigma=args.enigma, enigma_cfg=enigma_cfg)
            print(packaged)

    elif args.decrypt:
        if AESGCM is None:
            print("ERROR: cryptography package not found. Install with: pip install cryptography")
            return
        if not args.password:
            print("Password required (-p)")
            return
        if args.infile:
            with open(args.infile, "r", encoding="utf-8") as f:
                packaged = f.read().strip()
            try:
                out = decrypt(args.password, packaged)
                if args.outfile:
                    with open(args.outfile, "wb") as f:
                        f.write(out)
                    print("Saved plaintext to", args.outfile)
                else:
                    print(out.decode("utf-8", errors="replace"))
            except Exception as e:
                print("Decryption failed:", e)
        else:
            if not args.message:
                print("Provide packaged message with -m")
                return
            try:
                out = decrypt(args.password, args.message)
                print(out.decode("utf-8", errors="replace"))
            except Exception as e:
                print("Decryption failed:", e)
    else:
        parser.print_help()

if __name__ == "__main__":
    if AESGCM is None:
        print("ERROR: cryptography package not found. Install with: pip install cryptography")
        sys.exit(1)
    main_cli()
input("\nPress Enter to exit...")
