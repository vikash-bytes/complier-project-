"""
=============================================================
  PHASE 4 & 5: CONTROL FLOW ANALYSIS + FLOWCHART GENERATION
=============================================================
PURPOSE:
  This module takes the CFG (Control Flow Graph) and renders it
  as a graphical flowchart using Graphviz — the industry-standard
  graph visualization library.

FLOWCHART ELEMENT MAPPING:
  ┌─────────────────────────────────────────────────────────┐
  │  CFG Concept          →  Flowchart Shape                │
  ├─────────────────────────────────────────────────────────┤
  │  Entry block (START)  →  Rounded rectangle (green)      │
  │  Terminal block (HLT) →  Rounded rectangle (red)        │
  │  Process block        →  Rectangle (blue)               │
  │  Decision block       →  Diamond (orange) [has CMP/JZ]  │
  │  Sequential edge      →  Solid arrow                    │
  │  Conditional TRUE     →  Green arrow, label "Yes"       │
  │  Conditional FALSE    →  Red arrow,   label "No"        │
  │  Jump edge            →  Dashed arrow                   │
  │  Loop back-edge       →  Curved dashed arrow (purple)   │
  └─────────────────────────────────────────────────────────┘

HOW GRAPHVIZ WORKS:
  Graphviz uses the DOT language to describe graphs.
  We programmatically build a Digraph (directed graph),
  adding nodes and edges, then call .render() to produce PNG.

ANALOGY:
  Like a blueprint → the flowchart is the actual building.
=============================================================
"""

import os
from typing import Optional
import graphviz

from ir_generator import (
    CFG, BasicBlock,
    EDGE_SEQUENTIAL, EDGE_JUMP, EDGE_TRUE, EDGE_FALSE, EDGE_LOOP,
    CONDITIONAL_JUMPS,
)


# ── Visual style constants ──────────────────────────────────

# Node shapes and colors
STYLE_START = dict(shape="rectangle", style="rounded,filled",
                   fillcolor="#4CAF50", fontcolor="white",
                   penwidth="2", fontname="Helvetica-Bold")

STYLE_END   = dict(shape="rectangle", style="rounded,filled",
                   fillcolor="#F44336", fontcolor="white",
                   penwidth="2", fontname="Helvetica-Bold")

STYLE_PROCESS  = dict(shape="box", style="filled",
                      fillcolor="#2196F3", fontcolor="white",
                      fontname="Helvetica", penwidth="1.5")

STYLE_DECISION = dict(shape="diamond", style="filled",
                      fillcolor="#FF9800", fontcolor="white",
                      fontname="Helvetica-Bold", penwidth="2")

# Edge styles
EDGE_STYLES = {
    EDGE_SEQUENTIAL: dict(color="#555555", penwidth="1.5"),
    EDGE_JUMP:       dict(color="#9C27B0", style="dashed", penwidth="1.5"),
    EDGE_TRUE:       dict(color="#4CAF50", penwidth="2",
                          label=" Yes ", fontcolor="#4CAF50", fontname="Helvetica-Bold"),
    EDGE_FALSE:      dict(color="#F44336", penwidth="2",
                          label=" No ",  fontcolor="#F44336", fontname="Helvetica-Bold"),
    EDGE_LOOP:       dict(color="#9C27B0", style="dashed", penwidth="2",
                          label=" Loop ", fontcolor="#9C27B0",
                          fontname="Helvetica-Bold", constraint="false"),
}


def _block_label(block: BasicBlock) -> str:
    """
    Build the text label displayed inside a flowchart node.
    Includes the block's label name (if any) and all instructions.
    """
    lines = []

    # Show label name as header
    if block.label:
        lines.append(f"⬤ {block.label}")
        lines.append("─" * max(len(block.label) + 4, 12))

    # Show each instruction
    for instr in block.instructions:
        ops = ", ".join(instr.operands)
        lines.append(f"{instr.opcode}  {ops}" if ops else instr.opcode)

    return "\n".join(lines) if lines else block.id


def _is_decision_block(block: BasicBlock) -> bool:
    """
    A block is a DECISION block if its last instruction is a conditional jump.
    These get rendered as diamond (rhombus) shapes in the flowchart.
    """
    if not block.instructions:
        return False
    return block.instructions[-1].opcode in CONDITIONAL_JUMPS


def _is_terminal_block(block: BasicBlock, cfg: CFG) -> bool:
    """
    A block is TERMINAL if it has no outgoing edges (HLT, RET, or program end).
    These become the END node in the flowchart.
    """
    outgoing = [e for e in cfg.edges if e.from_block == block.id]
    return len(outgoing) == 0


def _is_entry_block(block_id: str, cfg: CFG) -> bool:
    """Entry block is the one with no incoming edges (or designated by CFG.entry)."""
    return block_id == cfg.entry


class FlowchartGenerator:
    """
    Converts a CFG into a Graphviz Digraph and renders it to PNG.

    Usage:
      gen = FlowchartGenerator(cfg)
      gen.generate("output/flowchart")   # saves output/flowchart.png
    """

    def __init__(self, cfg: CFG, title: str = "Assembly Flowchart"):
        self.cfg = cfg
        self.title = title
        self.dot = graphviz.Digraph(
            name="Assembly_Flowchart",
            comment="Generated by Assembly-to-Flowchart Compiler",
        )
        self._configure_graph()

    def _configure_graph(self):
        """Set global graph attributes for a clean, professional look."""
        self.dot.attr(
            rankdir="TB",          # Top-to-Bottom layout
            label=f"\n{self.title}\n(Generated by Assembly-to-Flowchart Compiler)",
            labelloc="t",          # Title at top
            fontsize="16",
            fontname="Helvetica-Bold",
            bgcolor="#FAFAFA",
            pad="0.5",
            nodesep="0.6",
            ranksep="0.8",
        )
        # Default node styling
        self.dot.attr("node", fontsize="11", margin="0.2,0.15")

    def generate(self, output_path: str = "output/flowchart") -> str:
        """
        Build the Graphviz digraph from CFG and render to PNG.

        Args:
          output_path: path WITHOUT extension. .png will be appended.

        Returns:
          The path to the generated PNG file.
        """
        self._add_nodes()
        self._add_edges()

        # Render — Graphviz writes a .dot source file + the PNG
        out = self.dot.render(
            filename=output_path,
            format="png",
            cleanup=True,   # remove intermediate .dot file
        )
        print(f"[FlowchartGenerator] Saved flowchart → {out}")
        return out

    def _add_nodes(self):
        """
        Add one Graphviz node per basic block with appropriate styling.

        Classification order:
          1. Entry (START)
          2. Terminal (END)
          3. Decision (diamond)
          4. Process (rectangle)
        """
        for block_id, block in self.cfg.blocks.items():
            label = _block_label(block)

            if _is_entry_block(block_id, self.cfg):
                # ── START node ──
                self.dot.node(block_id, label=label, **STYLE_START)

            elif _is_terminal_block(block, self.cfg):
                # ── END node ──
                self.dot.node(block_id, label=label, **STYLE_END)

            elif _is_decision_block(block):
                # ── DECISION (diamond) ──
                self.dot.node(block_id, label=label, **STYLE_DECISION)

            else:
                # ── PROCESS (rectangle) ──
                self.dot.node(block_id, label=label, **STYLE_PROCESS)

    def _add_edges(self):
        """
        Add directed edges between blocks with appropriate styling.
        Each CFGEdge becomes a Graphviz edge with color/label.
        """
        for edge in self.cfg.edges:
            style = EDGE_STYLES.get(edge.edge_type, {})
            self.dot.edge(edge.from_block, edge.to_block, **style)

    def get_dot_source(self) -> str:
        """Return the raw DOT language source (useful for debugging/learning)."""
        return self.dot.source


# ── Quick self-test ────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from lexer import Lexer
    from parser import Parser
    from ir_generator import IRGenerator

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

    os.makedirs("../output", exist_ok=True)
    gen = FlowchartGenerator(cfg)
    gen.generate("../output/flowchart")
