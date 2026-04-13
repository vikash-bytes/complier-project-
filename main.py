"""
=============================================================
  MAIN COMPILER PIPELINE
  Assembly-to-Flowchart Compiler
=============================================================

  This script is the entry point. It wires together all
  compilation phases in sequence:

  ┌──────────────┐
  │  Source Code │  (Assembly text)
  └──────┬───────┘
         │  Phase 1
         ▼
  ┌──────────────┐
  │    Lexer     │  Tokenization
  └──────┬───────┘
         │  Phase 2
         ▼
  ┌──────────────┐
  │    Parser    │  Syntax Analysis → AST
  └──────┬───────┘
         │  Phase 3
         ▼
  ┌──────────────┐
  │ IR Generator │  Control Flow Graph
  └──────┬───────┘
         │  Phase 4/5
         ▼
  ┌──────────────────┐
  │ Flowchart Gen    │  Graphviz → PNG
  └──────────────────┘

USAGE:
  python main.py                    # runs built-in sample
  python main.py my_program.asm     # reads from file

=============================================================
"""

import sys
import os

# Make sure src/ is on the path when running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from lexer import Lexer, LexerError
from parser import Parser, ParseError
from ir_generator import IRGenerator
from flowchart_generator import FlowchartGenerator


# ── Built-in sample programs ───────────────────────────────

SAMPLE_1 = """
; ================================================
; Sample 1: Conditional Branch + Loop
; Counts AX from 5 up to 10, then decrements once
; ================================================
START:
    MOV AX, 5        ; Initialize AX = 5
    CMP AX, 10       ; Compare AX with 10
    JZ EQUAL         ; Jump to EQUAL if AX == 10
    ADD AX, 1        ; AX = AX + 1
    JMP START        ; Loop back to START
EQUAL:
    SUB AX, 1        ; Decrement AX by 1
    HLT              ; Stop execution
"""

SAMPLE_2 = """
; ================================================
; Sample 2: Simple Loop with LOOP instruction
; Counts down from 5 to 0
; ================================================
INIT:
    MOV CX, 5        ; CX = loop counter = 5
LOOPSTART:
    DEC CX           ; Decrement counter
    CMP CX, 0        ; Check if zero
    JZ DONE          ; Exit if done
    JMP LOOPSTART    ; Otherwise loop
DONE:
    MOV AX, 1        ; Set result flag
    HLT
"""

SAMPLE_3 = """
; ================================================
; Sample 3: Arithmetic sequence
; ================================================
BEGIN:
    MOV AX, 10
    MOV BX, 3
    SUB AX, BX
    ADD AX, 7
    CMP AX, 14
    JZ SUCCESS
    JMP FAIL
SUCCESS:
    MOV BX, 1
    HLT
FAIL:
    MOV BX, 0
    HLT
"""

SAMPLES = {
    "1": ("conditional_loop",       SAMPLE_1, "Conditional Branch + Loop"),
    "2": ("simple_loop",            SAMPLE_2, "Simple LOOP Countdown"),
    "3": ("arithmetic_branch",      SAMPLE_3, "Arithmetic + Multi-Branch"),
}


def compile_assembly(source: str, output_path: str, title: str = "Assembly Flowchart"):
    """
    Run the full compiler pipeline on the given assembly source.

    Args:
      source      : raw assembly code string
      output_path : path (without extension) for the output PNG
      title       : label shown at top of the flowchart

    Returns:
      path to generated PNG, or None on error
    """

    print("\n" + "=" * 60)
    print("  Assembly-to-Flowchart Compiler")
    print("=" * 60)

    # ── PHASE 1: Lexical Analysis ──────────────────────────
    print("\n[Phase 1] Lexical Analysis...")
    try:
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        print(f"  ✓ {len(tokens)} tokens produced")
        for tok in tokens:
            print(f"    {tok}")
    except LexerError as e:
        print(f"  ✗ Lexer Error: {e}")
        return None

    # ── PHASE 2: Syntax Analysis ───────────────────────────
    print("\n[Phase 2] Syntax Analysis (Parsing)...")
    try:
        parser = Parser(tokens)
        ast = parser.parse()
        print(f"  ✓ {len(ast)} AST nodes produced")
        for node in ast:
            print(f"    {node}")
    except ParseError as e:
        print(f"  ✗ Parse Error: {e}")
        return None

    # ── PHASE 3: IR Generation (CFG) ──────────────────────
    print("\n[Phase 3] Intermediate Representation (CFG)...")
    try:
        ir_gen = IRGenerator(ast)
        cfg = ir_gen.generate()
        print(f"  ✓ {len(cfg.blocks)} basic blocks, {len(cfg.edges)} edges")
        for block in cfg.blocks.values():
            print(f"    {block}")
        for edge in cfg.edges:
            print(f"    {edge}")
    except Exception as e:
        print(f"  ✗ IR Error: {e}")
        raise

    # ── PHASE 4/5: Flowchart Generation ───────────────────
    print("\n[Phase 4/5] Generating Flowchart...")
    try:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        gen = FlowchartGenerator(cfg, title=title)

        # Optionally print DOT source for learning
        print("\n  [DOT source (Graphviz intermediate)]")
        for line in gen.get_dot_source().splitlines():
            print(f"    {line}")

        out_file = gen.generate(output_path)
        print(f"\n  ✓ Flowchart saved → {out_file}")
        return out_file
    except Exception as e:
        print(f"  ✗ Flowchart Error: {e}")
        raise


def main():
    """Entry point — handles CLI args and runs compilation."""

    # ── If a .asm file path is provided ───────────────────
    if len(sys.argv) > 1:
        asm_file = sys.argv[1]
        if not os.path.exists(asm_file):
            print(f"Error: File '{asm_file}' not found.")
            sys.exit(1)
        with open(asm_file, "r") as f:
            source = f.read()
        base = os.path.splitext(os.path.basename(asm_file))[0]
        compile_assembly(source, f"output/{base}", title=f"Flowchart: {base}")
        return

    # ── Otherwise run ALL built-in samples ────────────────
    print("\nNo input file provided — running all built-in samples.\n")

    for key, (filename, source, title) in SAMPLES.items():
        print(f"\n{'─'*60}")
        print(f"  Sample {key}: {title}")
        print(f"{'─'*60}")
        compile_assembly(source, f"output/{filename}", title=title)

    print("\n✅ All samples compiled! Check the output/ folder for PNG files.\n")


if __name__ == "__main__":
    main()
