"""
=============================================================
  PHASE 1: LEXICAL ANALYSIS (Lexer / Scanner)
=============================================================
PURPOSE:
  The Lexer is the first stage of the compiler pipeline.
  It reads raw source code (assembly text) character by character
  and groups them into meaningful units called TOKENS.

  A TOKEN is a categorized chunk of text, e.g.:
    - "MOV"  → INSTRUCTION token
    - "AX"   → REGISTER token
    - "5"    → NUMBER token
    - "START:"→ LABEL token

ANALOGY:
  Like reading a sentence and identifying words as
  nouns, verbs, numbers — before understanding grammar.
=============================================================
"""

import re
from dataclasses import dataclass
from typing import List


# ── Token Types ────────────────────────────────────────────
# Each category describes what a piece of text "means"
TOKEN_TYPES = {
    "LABEL":       r"^[A-Z_][A-Z0-9_]*:$",        # e.g.  START:  EQUAL:
    "INSTRUCTION": r"^(MOV|ADD|SUB|MUL|DIV|CMP|JMP|JZ|JNZ|JG|JL|JGE|JLE|LOOP|INC|DEC|NOP|HLT|PUSH|POP|CALL|RET)$",
    "REGISTER":    r"^(AX|BX|CX|DX|SI|DI|SP|BP|AL|AH|BL|BH|CL|CH|DL|DH)$",
    "NUMBER":      r"^-?\d+$",                     # e.g.  5  -3  100
    "LABEL_REF":   r"^[A-Z_][A-Z0-9_]*$",         # e.g.  START  EQUAL  (used as jump target)
    "COMMA":       r"^,$",                          # argument separator
    "COMMENT":     r"^;.*$",                        # ; this is a comment
}


@dataclass
class Token:
    """Represents a single token with its type and value."""
    type: str    # e.g. "INSTRUCTION", "REGISTER"
    value: str   # the actual text, e.g. "MOV", "AX"
    line: int    # source line number (for error reporting)

    def __repr__(self):
        return f"Token({self.type}, '{self.value}', line={self.line})"


class LexerError(Exception):
    """Raised when an unrecognised token is encountered."""
    pass


class Lexer:
    """
    Converts raw assembly source text into a flat list of Token objects.

    How it works:
      1. Split source into lines
      2. For each line, strip comments then split on whitespace/commas
      3. Match each piece against TOKEN_TYPES patterns
      4. Return list of Token objects
    """

    def __init__(self, source: str):
        self.source = source.upper()   # Assembly is case-insensitive → normalise to uppercase
        self.tokens: List[Token] = []

    def tokenize(self) -> List[Token]:
        """Main entry point — tokenizes entire source, returns token list."""
        lines = self.source.strip().split("\n")

        for line_num, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()

            # Skip blank lines
            if not line:
                continue

            # Strip inline comments (everything after ';')
            if ";" in line:
                line = line[:line.index(";")].strip()
            if not line:
                continue

            # Split line into raw pieces:
            #   "MOV AX, 5"  →  ["MOV", "AX,", "5"]
            # We handle comma as a separator by splitting on comma+space
            line = line.replace(",", " , ")    # pad commas so they split cleanly
            pieces = line.split()

            for piece in pieces:
                token = self._classify(piece, line_num)
                if token:
                    self.tokens.append(token)

        return self.tokens

    def _classify(self, piece: str, line_num: int) -> Token:
        """
        Try to match a text piece against each token pattern.
        Returns a Token, or raises LexerError if nothing matches.
        """
        for token_type, pattern in TOKEN_TYPES.items():
            if re.match(pattern, piece):
                return Token(type=token_type, value=piece, line=line_num)

        raise LexerError(
            f"Line {line_num}: Unrecognised token '{piece}'"
        )


# ── Quick self-test ────────────────────────────────────────
if __name__ == "__main__":
    sample = """
    START:
        MOV AX, 5
        CMP AX, 10
        JZ EQUAL
        ADD AX, 1
        JMP START
    EQUAL:
        SUB AX, 1
        HLT
    """
    lexer = Lexer(sample)
    tokens = lexer.tokenize()
    print("=== LEXER OUTPUT ===")
    for tok in tokens:
        print(tok)
