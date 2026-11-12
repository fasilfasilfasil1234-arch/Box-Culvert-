import math
import pythoncom
from win32com.client import VARIANT


class Geometry:

    def __init__(self, staad):

        self.geometry = staad.Geometry
        self.property = staad.Property

        self.geometry._FlagAsMethod("GetBeamLength")
        self.geometry._FlagAsMethod("GetNoOfSelectedNodes")
        self.geometry._FlagAsMethod("GetSelectedNodes")
        self.geometry._FlagAsMethod("GetNoOfSelectedBeams")
        self.geometry._FlagAsMethod("GetSelectedBeams")
        self.geometry._FlagAsMethod("CreateBeam")
        self.geometry._FlagAsMethod("GetMemberIncidence")
        self.geometry._FlagAsMethod("GetNodeCoordinates")
        self.geometry._FlagAsMethod("CreateGroup")
        self.geometry._FlagAsMethod("GetGroupCount")
        self.geometry._FlagAsMethod("GetGroupNames")
        self.geometry._FlagAsMethod("SelectMultipleNodes")
        self.geometry._FlagAsMethod("ClearNodeSelection")
        self.geometry._FlagAsMethod("SelectMultipleBeams")
        self.geometry._FlagAsMethod("ClearMemberSelection")
        self.property._FlagAsMethod("GetBetaAngle")

    def GetBeamLength(self, beam_no):

        length = self.geometry.GetBeamLength(beam_no)

        return round(length, 3)
    def GetBeamLength(self, beam_no):
    
        return round(
            self.geometry.GetBeamLength(beam_no),
            3
        )

    def CreateNode(self, node_no, x, y, z):

        self.geometry.CreateNode(
            node_no,
            x,
            y,
            z
        )

    def CreateBeam(self, beam_no, node_a, node_b):

        self.geometry.CreateBeam(
            beam_no,
            node_a,
            node_b
        )
        
    def GetLastNodeNo(self):
        return self.geometry.GetLastNodeNo

    def GetLastBeamNo(self):
        return self.geometry.GetLastBeamNo

    def GetSelectedNodes(self):

        count = int(self.geometry.GetNoOfSelectedNodes())

        if count == 0:
            return []

        nodes = VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_BYREF | pythoncom.VT_I4,
            [0] * count
        )

        # 0 = in the order of selection
        self.geometry.GetSelectedNodes(nodes, 0)

        return list(nodes.value)

    def GetSelectedBeams(self):

        count = int(self.geometry.GetNoOfSelectedBeams())

        if count == 0:
            return []

        beams = VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_BYREF | pythoncom.VT_I4,
            [0] * count
        )

        # 0 = in the order of selection
        self.geometry.GetSelectedBeams(beams, 0)

        return list(beams.value)

    def CreateMember(self, beam_no, node_a, node_b, start, end):

        # start and end are (x, y, z) coordinate tuples
        self.CreateNode(node_a, start[0], start[1], start[2])
        self.CreateNode(node_b, end[0], end[1], end[2])

        self.CreateBeam(beam_no, node_a, node_b)

        return beam_no

    def _GetNodeCoordinates(self, node_no):

        x = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_R8, 0.0)
        y = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_R8, 0.0)
        z = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_R8, 0.0)

        self.geometry.GetNodeCoordinates(node_no, x, y, z)

        return (x.value, y.value, z.value)

    def GetBeamLocalAxisCosines(self, beam_no):

        # --- end nodes and their coordinates ---
        node_a = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
        node_b = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
        self.geometry.GetMemberIncidence(beam_no, node_a, node_b)

        x1, y1, z1 = self._GetNodeCoordinates(node_a.value)
        x2, y2, z2 = self._GetNodeCoordinates(node_b.value)

        dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
        length = math.sqrt(dx * dx + dy * dy + dz * dz)

        # --- local x axis = member longitudinal direction ---
        lx, ly, lz = dx / length, dy / length, dz / length

        # --- default local y axis (perpendicular to x) ---
        if abs(lx) < 1e-4 and abs(ly) < 1e-4:
            yx, yy, yz = 0.0, 1.0, 0.0
        else:
            yx, yy, yz = -ly, lx, 0.0

        ny = math.sqrt(yx * yx + yy * yy + yz * yz)
        yx, yy, yz = yx / ny, yy / ny, yz / ny

        # --- local z axis = local x cross local y ---
        zx = ly * yz - lz * yy
        zy = lz * yx - lx * yz
        zz = lx * yy - ly * yx

        # --- apply beta rotation about local x (0 if no beta is set) ---
        beta = math.radians(self.property.GetBetaAngle(beam_no))
        cb, sb = math.cos(beta), math.sin(beta)

        local_x = (lx, ly, lz)
        local_y = (
            yx * cb + zx * sb,
            yy * cb + zy * sb,
            yz * cb + zz * sb
        )
        local_z = (
            -yx * sb + zx * cb,
            -yy * sb + zy * cb,
            -yz * sb + zz * cb
        )

        # add 0.0 to normalise any "-0.0" to "0.0"
        return {
            "local_x": tuple(round(c, 4) + 0.0 for c in local_x),
            "local_y": tuple(round(c, 4) + 0.0 for c in local_y),
            "local_z": tuple(round(c, 4) + 0.0 for c in local_z)
        }

    def _NextGroupName(self, group_type, prefix):

        # scan existing group names of this type and pick the next "prefix_N"
        count = int(self.geometry.GetGroupCount(group_type))

        max_n = 0
        if count > 0:
            names = VARIANT(
                pythoncom.VT_ARRAY | pythoncom.VT_BYREF | pythoncom.VT_BSTR,
                [""] * count
            )
            self.geometry.GetGroupNames(group_type, names)

            token = (prefix + "_").upper()   # STAAD stores names in upper-case
            for name in names.value:
                text = name.upper()
                if text.startswith(token):
                    suffix = text[len(token):]
                    if suffix.isdigit():
                        max_n = max(max_n, int(suffix))

        return prefix + "_" + str(max_n + 1)

    def CreateMemberGroupFromSelection(self):

        # groups the members currently selected in the STAAD GUI
        if int(self.geometry.GetNoOfSelectedBeams()) == 0:
            return None

        name = self._NextGroupName(2, "MemberGroup")
        self.geometry.CreateGroup(2, name)   # 2 = Members

        return name

    def CreateMemberGroupFromList(self, members):

        # groups an explicit list of member numbers
        self.geometry.ClearMemberSelection()

        selection = VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_BYREF | pythoncom.VT_I4,
            list(members)
        )
        self.geometry.SelectMultipleBeams(selection)

        name = self._NextGroupName(2, "MemberGroup")
        self.geometry.CreateGroup(2, name)   # 2 = Members

        return name

    def CreateNodeGroupFromSelection(self):

        # groups the nodes currently selected in the STAAD GUI
        if int(self.geometry.GetNoOfSelectedNodes()) == 0:
            return None

        name = self._NextGroupName(1, "NodeGroup")
        self.geometry.CreateGroup(1, name)   # 1 = Nodes

        return name

    def CreateNodeGroupFromList(self, nodes):

        # groups an explicit list of node numbers
        self.geometry.ClearNodeSelection()

        selection = VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_BYREF | pythoncom.VT_I4,
            list(nodes)
        )
        self.geometry.SelectMultipleNodes(selection)

        name = self._NextGroupName(1, "NodeGroup")
        self.geometry.CreateGroup(1, name)   # 1 = Nodes

        return name