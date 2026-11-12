"""
DECK_SLAB.PY - one axle of an IRC vehicle on a one-way deck slab -> line load
=============================================================================

Reusable (culvert top slab, solid slab bridge deck ...). No STAAD, no Excel.

For one axle at position x along the span it returns the dispersed patch on
a 1 m design strip: start, end, intensity (with and without impact), plus
every intermediate value so a calculation sheet can print the working.

Clauses (PDFs in "IRC codes/", checked 31 Oct 2026)
---------------------------------------------------
IRC:112-2020 Annex B-3
  B3.2(1)(i)   b_eff = alpha*a*(1 - a/l0) + b1
               a  = distance of the load centre from the nearer support
               b1 = tyre width across + 2 x wearing coat (and fill, B3.4)
               alpha from b/l0, b = WIDTH OF THE SLAB (not the carriageway)
               b_eff <= actual slab width; near a free edge
               b_eff <= b_eff/2 + distance of the load from the edge
  B3.2(1)(ii)  loads in a line along the span: each load its own b_eff
  B3.2(1)(iii) loads side by side: sum of widths minus overlap
  B3.3         along the span: contact + 2 x overall slab depth incl. wearing surface
  B3.4         45 deg through fill and wearing coat, both directions
IRC:112-2020 cl 7.6.1.1  l0 = centre-to-centre of supports (framed / continuous)
IRC:6-2017 cl 208        impact; 208.5 Note: L = effective span of the member;
                         208.6: fill >= 0.6 m incl. road crust -> half impact
"""

from dataclasses import dataclass
from typing import Optional

# IRC:112-2020 Annex B-3 table: b/l0 -> (alpha simply supported, alpha continuous)
ALPHA_TABLE = [
    (0.1, 0.40, 0.40), (0.2, 0.80, 0.80), (0.3, 1.16, 1.16), (0.4, 1.48, 1.44),
    (0.5, 1.72, 1.68), (0.6, 1.96, 1.84), (0.7, 2.12, 1.96), (0.8, 2.24, 2.08),
    (0.9, 2.36, 2.16), (1.0, 2.48, 2.24), (1.1, 2.60, 2.28), (1.2, 2.64, 2.36),
    (1.3, 2.72, 2.40), (1.4, 2.80, 2.48), (1.5, 2.84, 2.48), (1.6, 2.88, 2.52),
    (1.7, 2.92, 2.56), (1.8, 2.96, 2.60), (1.9, 3.00, 2.60), (2.0, 3.00, 2.60),
]


def alpha(b_over_l0, continuous=True):
    """Linear interpolation in the Annex B-3 table; ends held (as the Excel ipol)."""
    col = 2 if continuous else 1
    t = ALPHA_TABLE
    if b_over_l0 <= t[0][0]:
        return t[0][col]
    if b_over_l0 >= t[-1][0]:
        return t[-1][col]
    for lo, hi in zip(t[:-1], t[1:]):
        if lo[0] <= b_over_l0 <= hi[0]:
            f = (b_over_l0 - lo[0]) / (hi[0] - lo[0])
            return lo[col] + f * (hi[col] - lo[col])


def impact_fraction(rule, span, fill_total):
    """
    IRC:6-2017 cl 208 impact as a fraction. span = effective span of the member
    (208.5 Note). fill_total = filling incl. road crust above the slab (208.6).
    """
    if rule == "70R_wheeled":                       # 208.3 (RCC)
        if span <= 12.0:
            i = 0.25                                # < 9 m: 25 %; 9-12 m: 25 %
        else:
            raise ValueError("70R wheeled impact for spans > 12 m follows Fig. 9 - not coded")
    elif rule == "70R_tracked":                     # 208.3 (RCC)
        if span <= 5.0:
            i = 0.25
        elif span < 9.0:
            i = 0.25 - (0.25 - 0.10) * (span - 5.0) / 4.0
        elif span <= 40.0:
            i = 0.10
        else:
            raise ValueError("70R tracked impact for spans > 40 m follows Fig. 9 - not coded")
    elif rule == "class_A":                         # 208.2 (RCC), 3 m to 45 m
        if 3.0 <= span <= 45.0:
            i = 4.5 / (6.0 + span)
        else:
            raise ValueError("Class A impact outside 3-45 m follows Fig. 9 - not coded")
    else:
        raise ValueError(f"unknown impact rule {rule!r}")
    if fill_total >= 0.6:                           # 208.6: "not less than 0.6 m"
        i *= 0.5
    return i


@dataclass
class DeckSlab:
    """The slab the vehicle runs on (one-way span along traffic)."""
    l0: float                      # m  effective span (c/c of supports, IRC:112 7.6.1.1)
    b: float                       # m  width of the slab perpendicular to l0 (Annex B-3)
    t_slab: float                  # m  overall slab depth (B3.3)
    fill_ll: float                 # m  fill + wearing coat used for 45 deg dispersion (B3.4)
    fill_total: float              # m  fill incl. road crust for the impact check (208.6)
    edge_to_kerb: float            # m  slab free edge to roadway face of kerb/barrier
                                   #    (= barrier width + slab extension beyond the barrier)
    continuous: bool = True        # Annex B-3 alpha column (box top slab: continuous)
    strip: float = 1.0             # m  design strip width


def union_length(intervals, lo, hi):
    """Length of the union of [a, b] intervals, clipped to [lo, hi]."""
    segs = sorted((max(a, lo), min(b, hi)) for a, b in intervals if min(b, hi) > max(a, lo))
    total, cur_a, cur_b = 0.0, None, None
    for a, b in segs:
        if cur_b is None or a > cur_b:
            if cur_b is not None:
                total += cur_b - cur_a
            cur_a, cur_b = a, b
        else:
            cur_b = max(cur_b, b)
    if cur_b is not None:
        total += cur_b - cur_a
    return total


def axle_patch(vehicle, slab, x, axle_load_kN, impact, contact_length=None,
               centre_on_span=True):
    """
    One axle with its centre at x (m from the left support) -> dict, or None if
    it does not load the span. contact_length overrides the Annex A value
    (e.g. 0.263 to reproduce an office sheet).

    centre_on_span=True (default): the axle counts only if its centre lies on
    the span (0 <= x <= l0); an axle centred over a support goes straight into
    the support. Its patch is still clipped at the supports.
    False: any axle whose dispersed patch touches the span counts (a = 0 for
    centres beyond a support - gives a narrow, very intense sliver).
    """
    if centre_on_span and not (0.0 <= x <= slab.l0):
        return None
    c = vehicle.contact_length(axle_load_kN) if contact_length is None else contact_length
    dL = c + 2.0 * (slab.t_slab + slab.fill_ll)                 # B3.3 + B3.4
    x1, x2 = x - dL / 2, x + dL / 2
    if x2 <= 0.0 or x1 >= slab.l0:
        return None

    a = max(0.0, min(x, slab.l0 - x))                           # B3.2(1)(i)
    al = alpha(slab.b / slab.l0, slab.continuous)
    groups = []
    for g in vehicle.wheel_groups:
        b1 = g.width + 2.0 * slab.fill_ll                       # B3.2 b1 + B3.4
        beff = al * a * (1.0 - a / slab.l0) + b1
        y = slab.edge_to_kerb + vehicle.kerb_clearance + g.centre   # from the free edge
        groups.append({"b1": b1, "beff": beff, "y": y})

    raw = [(g["y"] - g["beff"] / 2, g["y"] + g["beff"] / 2) for g in groups]
    sum_widths = sum(b - a_ for a_, b in raw)
    in_slab_unclipped = union_length(raw, -1e9, 1e9)
    bP = union_length(raw, 0.0, slab.b)                         # B3.2(1)(iii) + edge rule
    overlap = sum_widths - in_slab_unclipped
    edge_cut = in_slab_unclipped - bP

    q = axle_load_kN / (bP * dL)                                # kN/m2
    return {
        "x": x, "P": axle_load_kN, "contact": c, "dL": dL,
        "x1": max(0.0, x1), "x2": min(slab.l0, x2), "a": a, "alpha": al,
        "groups": groups, "sum_widths": sum_widths, "overlap": overlap,
        "edge_cut": edge_cut, "bP": bP, "q": q, "impact": impact,
        "q_imp": q * (1.0 + impact),
        "w": q * (1.0 + impact) * slab.strip,                  # kN/m on the strip
        "w_no_impact": q * slab.strip,
    }
