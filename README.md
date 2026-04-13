# Assembly-to-Flowchart Compiler
### Educational Compiler Project | Python + Graphviz

---

## 📁 Folder Structure

```
assembly_flowchart/
│
├── main.py                        ← Entry point (run this!)
│
├── src/
│   ├── lexer.py                   ← Phase 1: Lexical Analysis
│   ├── parser.py                  ← Phase 2: Syntax Analysis
│   ├── ir_generator.py            ← Phase 3: IR / CFG Generation
│   └── flowchart_generator.py     ← Phase 4/5: Flowchart Output
│
├── tests/
│   └── fibonacci_check.asm        ← Sample assembly input file
│
├── output/                        ← Generated flowchart PNGs appear here
│
└── README.md                      ← This file
```

---

## 🚀 How to Run

### 1. Install dependencies
```bash
pip install graphviz
```

Also install the **Graphviz system package**:
- **Linux:**  `sudo apt-get install graphviz`
- **macOS:**  `brew install graphviz`
- **Windows:** Download from https://graphviz.org/download/

### 2. Run all built-in samples
```bash
python main.py
```
This generates 3 PNG flowcharts in the `output/` folder.

### 3. Run your own assembly file
```bash
python main.py tests/fibonacci_check.asm
```

---

## 🔬 Compilation Phases Explained

| Phase | Module | Description |
|-------|--------|-------------|
| 1. Lexical Analysis | `lexer.py` | Converts raw text into Tokens |
| 2. Syntax Analysis | `parser.py` | Validates grammar, builds AST |
| 3. IR Generation | `ir_generator.py` | Builds Control Flow Graph (CFG) |
| 4. Control Flow Analysis | `ir_generator.py` | Detects loops, branches, jumps |
| 5. Flowchart Generation | `flowchart_generator.py` | Maps CFG to visual diagram |

---

## 🎨 Flowchart Legend

| Shape / Color | Meaning |
|---------------|---------|
| 🟢 Green rounded rectangle | START / Entry block |
| 🔴 Red rounded rectangle | END / Terminal block (HLT) |
| 🔷 Blue rectangle | Process block (MOV, ADD, SUB…) |
| 🟠 Orange diamond | Decision block (CMP + conditional jump) |
| → Solid grey arrow | Sequential execution |
| → Green arrow "Yes" | Conditional jump taken (TRUE) |
| → Red arrow "No" | Fall-through (FALSE branch) |
| ⤷ Purple dashed arrow | Loop back-edge / JMP |

---

## 📚 Supported Assembly Instructions

| Category | Instructions |
|----------|-------------|
| Data Transfer | MOV |
| Arithmetic | ADD, SUB, MUL, DIV, INC, DEC |
| Comparison | CMP |
| Unconditional Jump | JMP |
| Conditional Jumps | JZ, JNZ, JG, JL, JGE, JLE |
| Loop | LOOP |
| Stack | PUSH, POP |
| Control | NOP, HLT, CALL, RET |

---

## 💡 How This Demonstrates Compiler Concepts

1. **Lexical Analysis** — Same as in GCC/Clang: the source text is broken into tokens before any grammar checking.
2. **Recursive Descent Parsing** — A standard top-down parsing technique used in most modern compilers.
3. **AST (Abstract Syntax Tree)** — The structured representation that compilers operate on internally.
4. **Basic Blocks & CFG** — Used by virtually every optimizing compiler (LLVM IR is essentially a CFG).
5. **Back-edges → Loop Detection** — The basis for loop optimizations in production compilers.
6. **IR Independence** — The same CFG could be used to generate x86, ARM, or WASM — we generate flowcharts instead.
