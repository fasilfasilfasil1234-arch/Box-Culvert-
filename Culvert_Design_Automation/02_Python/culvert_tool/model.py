"""
MODEL.PY - the "results form" handed from stage to stage
=========================================================

Think of this as the output-cells block of an Excel sheet. Stage 1 fills
the geometry part, Stage 2 fills the springs part, Stage 3 the loads part.
A later stage READS what earlier stages wrote - nothing is re-typed and
nothing is read back from STAAD.

You never edit this file. It only changes if a new stage needs to pass on
a kind of result that has no place here yet (the delivery note will say so).

17 Oct 2026 layout (see stage1_geometry.py):
  nodes 1-4 = corners, 5-6 = inner wall faces on the base, 7.. = intermediate
  member 1 = top slab, 2 = left wall, 3 = right wall, 4.. = base slab pieces
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class Member:
    no: int        # STAAD member number
    a: int         # start node
    b: int         # end node
    zone: str      # "base", "left_wall", "top" or "right_wall"


@dataclass
class BoxModel:
    # ---- Stage 1: geometry inputs (copied from stage1_geometry INPUTS) ----
    clear_span: float = 0.0      # m  B, inside width between wall faces
    clear_height: float = 0.0    # m  D, inside height between slab faces
    t_top: float = 0.0           # m
    t_wall: float = 0.0          # m
    t_bot: float = 0.0           # m
    strip_width: float = 1.0     # m  width into the page

    # ---- Stage 1: results ----
    L: float = 0.0               # m  centreline span   = B + t_wall  (modelled base length)
    H: float = 0.0               # m  centreline height = D + t_top/2 + t_bot/2
    overall_width: float = 0.0   # m  outer face to outer face = B + 2 t_wall (soil contact width)
    nodes: Dict[int, Tuple[float, float]] = field(default_factory=dict)  # {node: (x, y)}
    members: List[Member] = field(default_factory=list)
    base_roles: Dict[int, str] = field(default_factory=dict)  # {node: "end"/"junction"/"intermediate"}
    corner_nodes: Dict[str, int] = field(default_factory=dict)  # "bottom_left", "top_left", ...
    section_refs: Dict[str, int] = field(default_factory=dict)  # {"top"/"wall"/"base": ref}
    material: str = ""
    density: float = 0.0         # kN/m3 concrete

    # ---- Stage 2: springs ----
    ks: float = 0.0                                   # kN/m3 modulus of subgrade reaction
    springs: List[dict] = field(default_factory=list) # one row per base node
    support_refs: Dict[str, int] = field(default_factory=dict)  # {"end"/"junction"/"intermediate": ref}

    # ---- Stage 3: loads ----
    load_cases: Dict[int, str] = field(default_factory=dict)    # {case no: title}
    load_values: Dict[str, float] = field(default_factory=dict) # key numbers for the calc sheet

    # ---- bookkeeping ----
    stages_done: List[int] = field(default_factory=list)
    extra: Dict[str, object] = field(default_factory=dict)  # spare slot for later stages

    # ---- handy look-ups for later stages ----
    def members_in(self, zone: str) -> List[Member]:
        """All members of one zone, in numbering order."""
        return [m for m in self.members if m.zone == zone]

    def member_ends(self, m: Member) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """((xa, ya), (xb, yb)) of a member."""
        return self.nodes[m.a], self.nodes[m.b]

    def member_length(self, m: Member) -> float:
        (xa, ya), (xb, yb) = self.member_ends(m)
        return ((xb - xa) ** 2 + (yb - ya) ** 2) ** 0.5

    def base_nodes(self) -> List[Tuple[int, float]]:
        """[(node, x)] of the base slab nodes, left to right."""
        nos = set()
        for m in self.members_in("base"):
            nos.update((m.a, m.b))
        return sorted(((n, self.nodes[n][0]) for n in nos), key=lambda t: t[1])
