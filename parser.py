"""
=============================================================
  PHASE 2: SYNTAX ANALYSIS (Parser)
=============================================================
PURPOSE:
  The Parser takes the flat list of tokens from the Lexer and
  checks that they follow the GRAMMAR RULES of assembly language.
  It groups tokens into meaningful INSTRUCTIONS (AST nodes).

  This project uses a simple LINE-BY-LINE parser since assembly
  grammar is regular (each line = one instruction).

GRAMMAR (informal BNF):
  program     → statement*
  statement   → label | instruction
  label       → LABEL_TOKEN
  instruction → INSTRUCTION REGISTER [, REGISTER|NUMBER]
              | INSTRUCTION LABEL_REF      (for jumps)
              | INSTRUCTION                (for NOP/HLT/RET)

OUTPUT:
  A list of ParsedInstruction objects — the Abstract Syntax Tree (AST).
  Each node carries: opcode, operands, and source line.

ANALOGY:
  Like checking that sentences follow grammar rules:
  "MOV AX, 5" is valid.
  "5 AX MOV"  is a syntax error.
=============================================================
"""

from dataclasses import dataclass, field
from typing import List, Optional
from lexer import Token, LexerError


class ParseError(Exception):
    """Raised when the token stream violates assembly grammar."""
    pass


@dataclass
class ParsedInstruction:
    """
    Represents one parsed assembly statement.

    Examples:
      ParsedInstruction("MOV", ["AX", "5"], line=2)
      ParsedInstruction("JZ",  ["EQUAL"],   line=4)
      ParsedInstruction("LABEL", ["START"], line=1)
    """
    opcode: str                    # The operation: MOV, ADD, JZ, or "LABEL"
    operands: List[str] = field(default_factory=list)
    line: int = 0

    def __repr__(self):
        ops = ", ".join(self.operands)
        return f"[Line {self.line:2d}] {self.opcode:<8} {ops}"


# Instructions that take TWO operands: MOV AX, 5
TWO_OPERAND_OPS = {"MOV", "ADD", "SUB", "MUL", "DIV", "CMP"}

# Instructions that take ONE operand: JMP START, LOOP END, INC AX
ONE_OPERAND_OPS = {"JMP", "JZ", "JNZ", "JG", "JL", "JGE", "JLE",
                   "LOOP", "INC", "DEC", "PUSH", "POP", "CALL"}

# Instructions that take ZERO operands: NOP, HLT, RET
ZERO_OPERAND_OPS = {"NOP", "HLT", "RET"}


class Parser:
    """
    Recursive-descent style parser for assembly token stream.

    Strategy:
      - Scan tokens line-by-line (group tokens that share the same line number)
      - For each line, identify if it's a LABEL or an INSTRUCTION
      - Validate operand count/types based on the opcode
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.ast: List[ParsedInstruction] = []

    def parse(self) -> List[ParsedInstruction]:
        """Parse all tokens and return the AST (list of instructions)."""
        # Group tokens by their source line number
        lines = self._group_by_line()

        for line_num, line_tokens in lines.items():
            instruction = self._parse_line(line_tokens, line_num)
            if instruction:
                self.ast.append(instruction)

        return self.ast

    def _group_by_line(self):
        """Group tokens by line number preserving order."""
        groups = {}
        for tok in self.tokens:
            groups.setdefault(tok.line, []).append(tok)
        return dict(sorted(groups.items()))

    def _parse_line(self, tokens: List[Token], line_num: int) -> Optional[ParsedInstruction]:
        """
        Parse a single line of tokens into one ParsedInstruction.

        Grammar decisions happen here:
          LABEL token alone → label declaration
          INSTRUCTION token → dispatch to operand parser
        """
        if not tokens:
            return None

        first = tokens[0]

        # ── LABEL declaration ──────────────────────────────
        if first.type == "LABEL":
            label_name = first.value.rstrip(":")   # strip the colon
            if len(tokens) > 1:
                raise ParseError(
                    f"Line {line_num}: Unexpected tokens after label '{label_name}'"
                )
            return ParsedInstruction("LABEL", [label_name], line=line_num)

        # ── INSTRUCTION ────────────────────────────────────
        if first.type == "INSTRUCTION":
            return self._parse_instruction(first.value, tokens[1:], line_num)

        raise ParseError(
            f"Line {line_num}: Expected instruction or label, got '{first.value}'"
        )

    def _parse_instruction(self, opcode: str, rest: List[Token], line_num: int) -> ParsedInstruction:
        """
        Validate operands based on the opcode category.
        rest = tokens after the opcode (commas already filtered).
        """
        # Filter out COMMA tokens — they're punctuation, not operands
        operand_tokens = [t for t in rest if t.type != "COMMA"]
        operands = [t.value for t in operand_tokens]

        # ── Two-operand instructions ───────────────────────
        if opcode in TWO_OPERAND_OPS:
            if len(operands) != 2:
                raise ParseError(
                    f"Line {line_num}: '{opcode}' expects 2 operands, got {len(operands)}"
                )
            for t in operand_tokens:
                if t.type not in ("REGISTER", "NUMBER", "LABEL_REF"):
                    raise ParseError(
                        f"Line {line_num}: Invalid operand type '{t.type}' for '{opcode}'"
                    )

        # ── One-operand instructions ───────────────────────
        elif opcode in ONE_OPERAND_OPS:
            if len(operands) != 1:
                raise ParseError(
                    f"Line {line_num}: '{opcode}' expects 1 operand, got {len(operands)}"
                )

        # ── Zero-operand instructions ──────────────────────
        elif opcode in ZERO_OPERAND_OPS:
            if len(operands) != 0:
                raise ParseError(
                    f"Line {line_num}: '{opcode}' expects no operands, got {len(operands)}"
                )

        return ParsedInstruction(opcode, operands, line=line_num)


# ── Quick self-test ────────────────────────────────────────
if __name__ == "__main__":
    from lexer import Lexer

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

    parser = Parser(tokens)
    ast = parser.parse()

    print("=== PARSER OUTPUT (AST) ===")
    for node in ast:
        print(node)
