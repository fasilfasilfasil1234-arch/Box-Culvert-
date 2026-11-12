"""
irc_live_load - IRC vehicle live loads on deck slabs (reusable, no STAAD).

  vehicles.py     IRC vehicles as data (70R wheeled L type so far)
  deck_slab.py    one axle -> dispersed line load (IRC:112 Annex B-3, IRC:6 cl 208)
  moving_load.py  step the whole vehicle across a span, keep the worst positions
"""

from .vehicles import IRC_70R_WHEELED_L, VEHICLES, Vehicle, WheelGroup, tread_width
from .deck_slab import DeckSlab, alpha, axle_patch, impact_fraction
from .moving_load import find_critical_positions, loads_at, screen
