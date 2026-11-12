"""
VEHICLES.PY - IRC standard vehicles as data (no structure-specific logic)
=========================================================================

Reusable for any deck slab / culvert / bridge tool. Each vehicle says:
  - its axles along the traffic direction (load, spacing),
  - how each axle's load is shared across the width (wheel groups),
  - the tread width that bears on the deck (for the contact length),
  - its minimum kerb clearance and impact rule.

Source: IRC:6-2017 (PDF in "IRC codes/"), checked 31 Oct 2026.
  Fig. 1  Class 70R wheeled: axles 8, 12, 12, 17, 17, 17, 17 t (total 100 t)
          spacings 3.96, 1.52, 2.13, 1.37, 3.05, 1.37 m
          (overhangs 0.61 front, 0.91 rear - not needed for loads)
          'L' type wheel arrangement: two dual-tyre groups, each 0.86 m wide
          (2 x 0.41 m tyres), 2.79 m overall -> group centres 1.93 m apart.
          Tyre size 0.41 x 0.61 (SA and BA). Max tyre pressure 5.273 kg/cm2.
  Fig. 1 Note 4   kerb to outer edge of wheel, C = 1.2 m (70R).
  Annex A Note 1  all axles take the same wheel pattern as the heaviest axle.
  Annex A Note 2  contact area from tyre load, tyre pressure and tread width.
  Annex A Note 3  tyre size = overall width x rim diameter; tread width =
                  overall width - 25 mm (tyres up to 225 mm), - 50 mm (wider).
  cl 208.3        70R wheeled impact (see deck_slab.impact_fraction).

Not yet here (later): 'M' and 'N' 70R wheel types, 70R bogie, 70R tracked,
Class A.
"""

from dataclasses import dataclass, field
from typing import List, Tuple

TYRE_PRESSURE_KG_CM2 = 5.273          # IRC:6 Fig. 1


def tread_width(overall_width_m):
    """IRC:6 Annex A Note 3: tread = overall - 25 mm (<= 225 mm) or - 50 mm (wider)."""
    w_mm = overall_width_m * 1000.0
    return (w_mm - 25.0 if w_mm <= 225.0 else w_mm - 50.0) / 1000.0


@dataclass
class WheelGroup:
    """One wheel group of an axle, seen across the traffic direction."""
    offset: float          # m, from the vehicle's outer tyre edge (kerb side) to the group's near edge
    width: float           # m, overall width across traffic (e.g. 0.86 dual tyre)
    n_tyres: int           # tyres in the group (for the bearing tread width)
    tyre_width: float      # m, overall width of one tyre (Annex A Note 3)

    @property
    def centre(self):
        return self.offset + self.width / 2

    @property
    def bearing_tread(self):
        """Total tread width bearing on the deck (m)."""
        return self.n_tyres * tread_width(self.tyre_width)


@dataclass
class Vehicle:
    name: str
    axle_loads_t: List[float]                 # front to rear, tonnes per axle
    spacings: List[float]                     # m between successive axles
    wheel_groups: List[WheelGroup]            # same pattern for every axle (Annex A Note 1)
    kerb_clearance: float                     # m, kerb face to outer tyre edge
    impact_rule: str                          # key for deck_slab.impact_fraction
    overall_width: float = 0.0                # m across traffic (for information)
    notes: List[str] = field(default_factory=list)

    def axle_x(self) -> List[float]:
        """Axle positions from the FRONT axle (m)."""
        xs = [0.0]
        for s in self.spacings:
            xs.append(xs[-1] + s)
        return xs

    @property
    def length(self):
        return sum(self.spacings)

    def axles(self, reverse=False) -> List[Tuple[float, float]]:
        """[(x from the first axle on the deck, load kN)]; reverse = travelling the other way."""
        xs = self.axle_x()
        loads = [t * 10.0 for t in self.axle_loads_t]            # 1 t = 10 kN (as the Excel)
        if reverse:
            L = xs[-1]
            return sorted(((L - x, p) for x, p in zip(xs, loads)), key=lambda t: t[0])
        return list(zip(xs, loads))

    def contact_length(self, axle_load_kN):
        """
        Contact length along traffic for one axle (m), IRC:6 Annex A Notes 2 and 3:
        wheel-group load / (tyre pressure x bearing tread width). All groups equal.
        """
        group_load_kg = axle_load_kN * 100.0 / len(self.wheel_groups)      # kN -> kg
        tread_cm = self.wheel_groups[0].bearing_tread * 100.0
        return group_load_kg / (TYRE_PRESSURE_KG_CM2 * tread_cm) / 100.0  # cm -> m


# -----------------------------------------------------------------------------
# IRC Class 70R wheeled, 'L' type wheel arrangement  (IRC:6-2017 Fig. 1)
# -----------------------------------------------------------------------------
IRC_70R_WHEELED_L = Vehicle(
    name="IRC Class 70R wheeled (L type)",
    axle_loads_t=[8, 12, 12, 17, 17, 17, 17],
    spacings=[3.96, 1.52, 2.13, 1.37, 3.05, 1.37],
    wheel_groups=[
        WheelGroup(offset=0.0, width=0.86, n_tyres=2, tyre_width=0.41),
        WheelGroup(offset=2.79 - 0.86, width=0.86, n_tyres=2, tyre_width=0.41),
    ],
    kerb_clearance=1.2,
    impact_rule="70R_wheeled",
    overall_width=2.79,
    notes=["Group centres 1.93 m apart (2.79 - 0.86).",
           "Tread per tyre 0.41 - 0.05 = 0.36 m; 0.72 m per dual group."],
)

VEHICLES = {"70R_wheeled_L": IRC_70R_WHEELED_L}
