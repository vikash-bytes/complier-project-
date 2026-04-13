"""
=============================================================
  PHASE 3: INTERMEDIATE REPRESENTATION (IR Generator)
=============================================================
PURPOSE:
  The IR Generator converts the AST (parsed instructions) into a
  Control Flow Graph (CFG) — a classic Intermediate Representation.

  A CFG consists of:
    - BASIC BLOCKS: sequences of instructions with no branches
      (execution enters at the top and exits at the bottom)
    - EDGES: directed connections showing possible control flow
      (sequential, conditional true/false, unconditional jump, loop)

WHY IR?
  IR is machine-independent. The same IR can be used to:
    - Generate flowcharts (our goal)
    - Optimize code
    - Generate machine code for different architectures

ALGORITHM (Leader detection):
  1. Identify "leader" instructions — start of each basic block:
     - First instruction
     - Any instruction that is a jump TARGET (label)
     - Any instruction immediately AFTER a jump
  2. Group instructions between leaders into basic blocks
  3. Analyze jump instructions to create edges between blocks

ANALOGY:
  Breaking a chapter into paragraphs, then drawing arrows
  showing which paragraph you go to next.
=============================================================
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from parser import ParsedInstruction


# ── Edge types ─────────────────────────────────────────────
EDGE_SEQUENTIAL = "sequential"   # normal fall-through
EDGE_JUMP       = "jump"         # unconditional JMP
EDGE_TRUE       = "true"         # conditional jump taken
EDGE_FALSE      = "false"        # conditional jump NOT taken (fall-through)
EDGE_LOOP       = "loop"         # LOOP instruction back-edge


@dataclass
class BasicBlock:
    """
    A Basic Block is a maximal sequence of instructions with:
      - Exactly ONE entry point (first instruction)
      - Exactly ONE exit point (last instruction)
      - No jumps in the middle

    Attributes:
      id         : Unique block identifier (e.g. "B0", "B1")
      instructions: The list of instructions in this block
      label      : Optional label name if this block starts at a label
    """
    id: str
    instructions: List[ParsedInstruction] = field(default_factory=list)
    label: Optional[str] = None   # e.g. "START", "EQUAL"

    def __repr__(self):
        instr_str = " | ".join(
            f"{i.opcode} {' '.join(i.operands)}" for i in self.instructions
        )
        label_prefix = f"[{self.label}] " if self.label else ""
        return f"Block {self.id}: {label_prefix}{instr_str}"


@dataclass
class CFGEdge:
    """
    A directed edge in the Control Flow Graph.

    from_block → to_block with an edge_type label.
    """
    from_block: str    # block ID
    to_block: str      # block ID
    edge_type: str     # EDGE_* constant above

    def __repr__(self):
        return f"{self.from_block} --[{self.edge_type}]--> {self.to_block}"


class CFG:
    """
    The complete Control Flow Graph.

    Contains:
      blocks : dict of block_id → BasicBlock
      edges  : list of CFGEdge
      entry  : ID of the entry (first) block
    """
    def __init__(self):
        self.blocks: Dict[str, BasicBlock] = {}
        self.edges: List[CFGEdge] = []
        self.entry: Optional[str] = None

    def add_block(self, block: BasicBlock):
        self.blocks[block.id] = block
        if self.entry is None:
            self.entry = block.id   # first block added is the entry

    def add_edge(self, from_id: str, to_id: str, edge_type: str):
        self.edges.append(CFGEdge(from_id, to_id, edge_type))

    def __repr__(self):
        lines = ["=== CONTROL FLOW GRAPH ==="]
        for b in self.blocks.values():
            lines.append(str(b))
        lines.append("")
        for e in self.edges:
            lines.append(str(e))
        return "\n".join(lines)


# ── Conditional jump opcodes ───────────────────────────────
CONDITIONAL_JUMPS = {"JZ", "JNZ", "JG", "JL", "JGE", "JLE"}
UNCONDITIONAL_JUMPS = {"JMP"}
ALL_JUMPS = CONDITIONAL_JUMPS | UNCONDITIONAL_JUMPS | {"LOOP"}


class IRGenerator:
    """
    Converts the AST (list of ParsedInstructions) into a CFG.

    Steps:
      1. Build a label→index map (which instruction index each label points to)
      2. Find "leader" indices (start of each basic block)
      3. Partition instructions into BasicBlocks
      4. Connect blocks with CFGEdges based on control flow
    """

    def __init__(self, ast: List[ParsedInstruction]):
        self.ast = ast
        self.cfg = CFG()
        self._label_map: Dict[str, int] = {}   # label_name → instruction index
        self._block_start: Dict[int, str] = {} # instr_index → block_id

    def generate(self) -> CFG:
        """Run all IR-generation steps."""
        self._build_label_map()
        leaders = self._find_leaders()
        self._build_blocks(leaders)
        self._add_edges()
        return self.cfg

    def _build_label_map(self):
        """
        Step 1: Scan AST for LABEL nodes, record which index follows each label.

        Example:
          index 0: LABEL START   → label_map["START"] = 1  (next real instruction)
          index 5: LABEL EQUAL   → label_map["EQUAL"] = 6
        """
        for i, instr in enumerate(self.ast):
            if instr.opcode == "LABEL":
                # The label points to the NEXT instruction
                self._label_map[instr.operands[0]] = i

    def _find_leaders(self) -> List[int]:
        """
        Step 2: Identify indices that start a new basic block (leaders).

        An instruction is a leader if:
          (a) It is the first instruction
          (b) It is the target of any jump (i.e., at a label)
          (c) It immediately follows a jump instruction
        """
        leaders = {0}   # rule (a): first instruction is always a leader

        for i, instr in enumerate(self.ast):
            opcode = instr.opcode

            if opcode in ALL_JUMPS:
                # rule (c): instruction AFTER a jump starts a new block
                if i + 1 < len(self.ast):
                    leaders.add(i + 1)

                # rule (b): jump target is a leader
                target_label = instr.operands[0]
                if target_label in self._label_map:
                    leaders.add(self._label_map[target_label])

            if opcode == "LABEL":
                # Labels themselves mark block boundaries
                leaders.add(i)

        return sorted(leaders)

    def _build_blocks(self, leaders: List[int]):
        """
        Step 3: Slice the instruction list at leader positions
                to create BasicBlock objects.
        """
        # Create block boundaries: each leader → next leader
        boundaries = list(zip(leaders, leaders[1:] + [len(self.ast)]))

        for block_idx, (start, end) in enumerate(boundaries):
            block_id = f"B{block_idx}"
            block = BasicBlock(id=block_id)

            # Check if this block starts with a label
            first_instr = self.ast[start]
            if first_instr.opcode == "LABEL":
                block.label = first_instr.operands[0]
                # Add instructions EXCEPT the label itself (it's metadata)
                block.instructions = [
                    i for i in self.ast[start + 1:end]
                    if i.opcode != "LABEL"
                ]
            else:
                block.instructions = [
                    i for i in self.ast[start:end]
                    if i.opcode != "LABEL"
                ]

            # Record which instruction indices belong to this block
            for idx in range(start, end):
                self._block_start[idx] = block_id

            self.cfg.add_block(block)

    def _add_edges(self):
        """
        Step 4: Connect basic blocks with directed edges.

        Logic:
          - After each block, check its LAST instruction:
            * JMP target     → unconditional jump edge to target block
            * JZ/JNZ/etc.    → true edge to target, false edge to next block
            * LOOP target    → loop back-edge to target
            * HLT/RET        → no outgoing edges (terminal)
            * otherwise      → sequential edge to next block
        """
        block_ids = list(self.cfg.blocks.keys())

        for i, block_id in enumerate(block_ids):
            block = self.cfg.blocks[block_id]

            if not block.instructions:
                # Empty block (label-only) — connect sequentially
                if i + 1 < len(block_ids):
                    self.cfg.add_edge(block_id, block_ids[i + 1], EDGE_SEQUENTIAL)
                continue

            last = block.instructions[-1]
            opcode = last.opcode

            # ── Terminal instructions ──────────────────────
            if opcode in ("HLT", "RET"):
                continue   # No outgoing edges → this is an END node

            # ── Unconditional jump ─────────────────────────
            elif opcode in UNCONDITIONAL_JUMPS:
                target_block = self._resolve_label(last.operands[0])
                if target_block:
                    # Detect loop: jumping backward
                    edge_type = EDGE_LOOP if target_block < block_id else EDGE_JUMP
                    self.cfg.add_edge(block_id, target_block, edge_type)

            # ── Conditional jumps ──────────────────────────
            elif opcode in CONDITIONAL_JUMPS:
                # TRUE branch: jump taken
                target_block = self._resolve_label(last.operands[0])
                if target_block:
                    self.cfg.add_edge(block_id, target_block, EDGE_TRUE)

                # FALSE branch: fall-through to next block
                if i + 1 < len(block_ids):
                    self.cfg.add_edge(block_id, block_ids[i + 1], EDGE_FALSE)

            # ── LOOP instruction ───────────────────────────
            elif opcode == "LOOP":
                target_block = self._resolve_label(last.operands[0])
                if target_block:
                    self.cfg.add_edge(block_id, target_block, EDGE_LOOP)
                # Fall-through when loop counter reaches zero
                if i + 1 < len(block_ids):
                    self.cfg.add_edge(block_id, block_ids[i + 1], EDGE_FALSE)

            # ── Sequential fall-through ────────────────────
            else:
                if i + 1 < len(block_ids):
                    self.cfg.add_edge(block_id, block_ids[i + 1], EDGE_SEQUENTIAL)

    def _resolve_label(self, label_name: str) -> Optional[str]:
        """Map a label name to the block ID that starts at that label."""
        if label_name not in self._label_map:
            return None
        instr_idx = self._label_map[label_name]
        return self._block_start.get(instr_idx)


# ── Quick self-test ────────────────────────────────────────
if __name__ == "__main__":
    from lexer import Lexer
    from parser import Parser

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
    tokens = Lexer(sample).tokenize()
    ast    = Parser(tokens).parse()
    cfg    = IRGenerator(ast).generate()

    print(cfg)
