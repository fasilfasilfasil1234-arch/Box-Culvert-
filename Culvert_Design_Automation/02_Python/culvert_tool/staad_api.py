"""
STAAD_API.PY - shared OpenSTAAD helpers used by every stage
===========================================================

Connect, call-with-clear-error, units, empty-model check, view refresh,
and the comtypes pattern for passing arrays in and out of OpenSTAAD.

This file does NOT create or save STAAD files. You open STAAD, set kN and
metres, save the file where you want, keep it open - and the stages model
into that open file. Save it yourself in STAAD when you are happy.

Where each OpenSTAAD function was checked
-----------------------------------------
[L] = Bentley OpenSTAAD Help installed with YOUR STAAD.Pro CONNECT Edition
      22.00.00.15:  C:\\Program Files\\Bentley\\Engineering\\
      STAAD.Pro CONNECT Edition\\Help\\OSAPP  (checked 16 Oct 2026)
[R] = OpenSTAAD Reference Manual (Bentley, V8i SS4), Section 4.
[B] = Bentley STAAD.Pro Help, "Write an OpenSTAAD Program in Python"
      (connection, _FlagAsMethod, array pattern).
[T] = Tested live on your PC, 16 Oct 2026, read-only against the open
      twin-cell model (array read-back with SAFEARRAY.unpack()).

  comtypes.client.GetActiveObject("StaadPro.OpenSTAAD")   [B][T]
  <object>._FlagAsMethod("Name")                           [B][T]
  SetInputUnits(lUnit, fUnit)                              [L]  lUnit 4 = Meter, fUnit 5 = KiloNewton
  GetBaseUnit()                                            [L][T]  2 = metric
  Geometry.GetNodeCount() / GetMemberCount()               [L][T]
  UpdateStructure()                                        [L]
  View.SetLabel(which, showFlag)                           [L]  0 node no, 1 member no, 4 support, 8 load value
  View.ZoomAll()                                           [L]
"""

import ctypes

# OpenSTAAD codes  [L]
UNIT_METER = 4
UNIT_KILONEWTON = 5
LABEL_NODE_NUMBER = 0
LABEL_MEMBER_NUMBER = 1
LABEL_SUPPORT = 4
LABEL_LOAD_VALUE = 8

# COM error codes meaning the STAAD process is gone (RPC call failed / server unavailable)
RPC_LOST = (-2147023170, -2147023174)

LOCAL_HELP_HINT = (
    "Check this function's exact name/arguments in your local OpenSTAAD help:\n"
    "  C:\\Program Files\\Bentley\\Engineering\\STAAD.Pro CONNECT Edition\\Help\\"
    "OpenSTAAD_HELP_HOME.html\n"
    "  (or STAAD.Pro menu: Help > OpenSTAAD Help)"
)


class StopRun(Exception):
    """Raised by any stage to stop the run with a clear message (no crash dump)."""


# -----------------------------------------------------------------------------
# Connection and calls
# -----------------------------------------------------------------------------
def connect():
    """Connect to the STAAD.Pro window that is already open, with your model."""
    try:
        from comtypes import client
    except ImportError:
        raise StopRun("comtypes is not installed. Double-click setup.bat once.")
    try:
        return client.GetActiveObject("StaadPro.OpenSTAAD")             # [B][T]
    except Exception as exc:
        raise StopRun(
            "Could not connect to STAAD.Pro.\n"
            "  - Is STAAD.Pro open with your model file?\n"
            "  - Are Python and STAAD both 64-bit?\n"
            f"  Error: {exc}"
        )


def flag(obj, *names):
    """comtypes needs each OpenSTAAD method flagged before calling it  [B]."""
    for n in names:
        obj._FlagAsMethod(n)


def call(obj, name, *args):
    """Call an OpenSTAAD method; if it fails, say exactly which call failed."""
    try:
        return getattr(obj, name)(*args)
    except Exception as exc:  # COM errors come through as various types
        code = getattr(exc, "hresult", None) or (exc.args[0] if exc.args else None)
        if code in RPC_LOST:
            raise StopRun(
                f"STAAD.Pro stopped responding during {name} (it crashed or was closed).\n"
                "  Reopen STAAD with a NEW blank file (kN, m), save it, and run again.\n"
                "  Send me this whole console output, including the last 'creating ...' line."
            )
        print(f"\nOpenSTAAD call failed: {name}{args}")
        print(f"  Error: {exc}")
        print("  " + LOCAL_HELP_HINT.replace("\n", "\n  "))
        raise


def call_ok(obj, name, *args):
    """
    Call a function whose documented return is 0 = OK, negative = error  [L].
    A non-zero return is printed as a WARNING (not a stop): Bentley notes that
    some calls report failure even when they worked, so each stage confirms
    its work by reading the model back.
    """
    ret = call(obj, name, *args)
    try:
        bad = ret is not None and int(ret) < 0
    except (TypeError, ValueError):
        bad = False
    if bad:
        print(f"  WARNING: {name}{args} returned {ret} (checked by read-back below)")
    return ret


# -----------------------------------------------------------------------------
# Common steps
# -----------------------------------------------------------------------------
def set_units_m_kn(staad):
    """
    Set OpenSTAAD's INPUT units to metre and kN.
    You already set kN-m in the file; this makes sure the numbers the script
    sends are read as metres and kN too (CreateNode etc. use input units).
    """
    flag(staad, "SetInputUnits")
    call(staad, "SetInputUnits", UNIT_METER, UNIT_KILONEWTON)          # [L]


def require_empty_model(staad):
    """Stop if the open model already has nodes or members (prevents a duplicate frame)."""
    geo = staad.Geometry
    flag(geo, "GetNodeCount", "GetMemberCount")
    n_nodes = call(geo, "GetNodeCount") or 0                            # [L][T]
    n_mem = call(geo, "GetMemberCount") or 0                            # [L][T]
    if n_nodes or n_mem:
        raise StopRun(
            f"The open STAAD model already has {n_nodes} nodes and {n_mem} members.\n"
            "  Nothing was changed. To run again, open a fresh blank file\n"
            "  (kN, m), save it where you want, and run again."
        )


def refresh_view(staad, *labels):
    """Update the model in STAAD, switch on the given labels and zoom to fit."""
    flag(staad, "UpdateStructure")
    call(staad, "UpdateStructure")                                      # [L]
    view = staad.View
    flag(view, "SetLabel", "ZoomAll")
    for label in labels:
        call(view, "SetLabel", label, True)                             # [L]
    call(view, "ZoomAll")                                               # [L]


# -----------------------------------------------------------------------------
# Array pattern  [B][T]
# -----------------------------------------------------------------------------
def _automation():
    from comtypes import automation
    return automation


def make_variant_vt_ref(obj, var_type):
    """Wrap a ctypes object as a by-reference VARIANT, as in Bentley's example  [B]."""
    automation = _automation()
    var = automation.VARIANT()
    var._.c_void_p = ctypes.addressof(obj)
    var.vt = var_type | automation.VT_BYREF
    return var


def double_array_in(values):
    """
    Pass a list of numbers to OpenSTAAD as an array of doubles  [B].
    Returns (variant, keep). Hold on to 'keep' until the call is done,
    otherwise Python may free the memory STAAD is reading.
    """
    automation = _automation()
    sa = automation._midlSAFEARRAY(ctypes.c_double).create([float(v) for v in values])
    return make_variant_vt_ref(sa, automation.VT_ARRAY | automation.VT_R8), sa


def long_array_out(size):
    """Empty array of integers for OpenSTAAD to fill. Read it with read_array(keep)  [T]."""
    automation = _automation()
    sa = automation._midlSAFEARRAY(ctypes.c_long).create([0] * size)
    return make_variant_vt_ref(sa, automation.VT_ARRAY | automation.VT_I4), sa


def double_array_out(size):
    """Empty array of doubles for OpenSTAAD to fill. Read it with read_array(keep)  [T]."""
    automation = _automation()
    sa = automation._midlSAFEARRAY(ctypes.c_double).create([0.0] * size)
    return make_variant_vt_ref(sa, automation.VT_ARRAY | automation.VT_R8), sa


def read_array(keep):
    """Values STAAD wrote into an array (tested on your PC: SAFEARRAY.unpack())  [T]."""
    return list(keep.unpack())


def double_out():
    """Single double output argument. Returns (variant, ctypes value) - read .value  [B]."""
    automation = _automation()
    d = ctypes.c_double(0.0)
    return make_variant_vt_ref(d, automation.VT_R8), d


# -----------------------------------------------------------------------------
# Small formatting helper
# -----------------------------------------------------------------------------
def staad_list(numbers):
    """[1,2,3,5,7,8,9] -> '1 TO 3 5 7 TO 9' (STAAD list style)."""
    nums = sorted(set(int(n) for n in numbers))
    out, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        if j - i >= 2:
            out.append(f"{nums[i]} TO {nums[j]}")
        else:
            out.extend(str(n) for n in nums[i:j + 1])
        i = j + 1
    return " ".join(out)
