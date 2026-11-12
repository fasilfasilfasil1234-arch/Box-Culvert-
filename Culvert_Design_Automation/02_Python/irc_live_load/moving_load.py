"""
MOVING_LOAD.PY - step a whole IRC vehicle across a span, keep only the worst
============================================================================

Reusable. The full vehicle (all axles, IRC:6 cl 204.1.3) is moved along the
span in small steps, in both travel directions. At every step, each axle
whose dispersed patch lands on the span becomes a line load on the 1 m strip
(deck_slab.axle_patch); axles off the span are ignored automatically.

Each step is screened with simple beam formulas to find:
  SAG   - max sagging moment at mid-span       (simply supported beam)
  HOG   - max hogging moment at a support      (fixed-ended beam)
  SHEAR - max shear at the critical section     (simply supported beam)
          x_v from each support (e.g. wall face + effective depth)
The screening only CHOOSES the positions. The chosen positions go into the
real structural model (e.g. STAAD), which gives the design forces.

    from irc_live_load import IRC_70R_WHEELED_L, DeckSlab, find_critical_positions
    res = find_critical_positions(IRC_70R_WHEELED_L, slab, shear_section=0.55)
    res["SAG"]["patches"]  -> [{x1, x2, w, ...}, ...]
"""

from .deck_slab import axle_patch, impact_fraction

N_PIECES = 40          # each patch split into point loads for the screening


def loads_at(vehicle, slab, x_first, reverse=False, contact_length=None, impact=None,
             centre_on_span=True):
    """All axle patches with the first axle (in travel order) at x_first."""
    if impact is None:
        impact = impact_fraction(vehicle.impact_rule, slab.l0, slab.fill_total)
    out = []
    for dx, P in vehicle.axles(reverse):
        p = axle_patch(vehicle, slab, x_first + dx, P, impact, contact_length, centre_on_span)
        if p is not None:
            out.append(p)
    return out


def _points(patches):
    """Patches -> [(position, force kN)] for the screening."""
    pts = []
    for p in patches:
        n = N_PIECES
        dx = (p["x2"] - p["x1"]) / n
        for i in range(n):
            pts.append((p["x1"] + (i + 0.5) * dx, p["w"] * dx))
    return pts


def screen(patches, l, x_v):
    """Return (M mid SS, M support FF, V at x_v SS) for one set of patches."""
    pts = _points(patches)
    c = l / 2
    m_mid = sum(P * (a * (l - c) / l if a <= c else c * (l - a) / l) for a, P in pts)
    m_a = sum(P * a * (l - a) ** 2 / l ** 2 for a, P in pts)       # fixed-end moments
    m_b = sum(P * a ** 2 * (l - a) / l ** 2 for a, P in pts)
    r_a = sum(P * (l - a) / l for a, P in pts)
    r_b = sum(P * a / l for a, P in pts)
    v_a = r_a - sum(P for a, P in pts if a < x_v)                   # section x_v from left
    v_b = r_b - sum(P for a, P in pts if a > l - x_v)              # and from right
    return m_mid, max(m_a, m_b), max(abs(v_a), abs(v_b))


def find_critical_positions(vehicle, slab, shear_section, step=0.05, contact_length=None,
                            centre_on_span=True):
    """
    Step the vehicle through the span both ways. Returns
      {"SAG"|"HOG"|"SHEAR": {"value", "x_first", "reverse", "patches"}, "impact": i}
    shear_section = distance from each support to the shear check section (m).
    """
    impact = impact_fraction(vehicle.impact_rule, slab.l0, slab.fill_total)
    reach = vehicle.length + slab.l0 + 3.0                     # patches are < 3 m long
    best = {k: {"value": -1.0} for k in ("SAG", "HOG", "SHEAR")}
    n = int(round(2 * reach / step))
    for reverse in (False, True):
        for i in range(n + 1):
            x_first = -vehicle.length - 1.5 + i * step
            patches = loads_at(vehicle, slab, x_first, reverse, contact_length, impact,
                               centre_on_span)
            if not patches:
                continue
            vals = dict(zip(("SAG", "HOG", "SHEAR"), screen(patches, slab.l0, shear_section)))
            for k, v in vals.items():
                if v > best[k]["value"] + 1e-9:
                    best[k] = {"value": v, "x_first": x_first, "reverse": reverse,
                               "patches": patches}
    best["impact"] = impact
    return best
