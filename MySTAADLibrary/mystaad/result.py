import win32com.client
from win32com.client import VARIANT
import pythoncom


class Results:

    def __init__(self, staad, geometry):
        self.output = staad.Output
        self.geometry = geometry

        self.output._FlagAsMethod("GetMemberEndForces")
        self.output._FlagAsMethod("GetIntermediateMemberForcesAtDistance")
        self.output._FlagAsMethod("GetSupportReactions")
        self.output._FlagAsMethod("GetMemberDesignSectionName")
        self.output._FlagAsMethod("GetMemberSteelDesignRatio")
        self.output._FlagAsMethod("AreResultsAvailable")

    def AreResultsAvailable(self):

        return self.output.AreResultsAvailable()

    def GetMemberDesignSectionName(self, member_no):

        return self.output.GetMemberDesignSectionName(member_no)

    def GetMemberSteelDesignRatio(self, member_no):

        ratio = VARIANT(
            pythoncom.VT_BYREF | pythoncom.VT_R8,
            0.0
        )

        self.output.GetMemberSteelDesignRatio(
            member_no,
            ratio
        )

        return round(ratio.value,3)

    def GetMemberEndForces(self, member_no, end_no, load_case):

        forces = VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_BYREF | pythoncom.VT_R8,
            [0.0] * 6
        )

        self.output.GetMemberEndForces(
            member_no,
            end_no,
            load_case,
            forces
        )

        return tuple(round(x, 3) for x in forces.value)
    
    def GetIntermediateMemberForcesAtDistance(
        self,
        member_no,
        distance,
        load_case
    ):

        forces = VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_BYREF | pythoncom.VT_R8,
            [0.0] * 6
        )

        self.output.GetIntermediateMemberForcesAtDistance(
            member_no,
            distance,
            load_case,
            forces
        )

        return tuple(round(x, 3) for x in forces.value)
    
    def GetSupportReactions(
        self,
        support_node,
        load_case
    ):

        reactions = VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_BYREF | pythoncom.VT_R8,
            [0.0] * 6
        )

        self.output.GetSupportReactions(
            support_node,
            load_case,
            reactions
        )

        return tuple(round(x, 3) for x in reactions.value)
    
    def GetMemberDesignSummary(self, member_no):
    
        sec = self.output.GetMemberDesignSectionName(member_no)

        ratio = VARIANT(
            pythoncom.VT_BYREF | pythoncom.VT_R8,
            0.0
        )

        self.output.GetMemberSteelDesignRatio(
            member_no,
            ratio
        )

        return {
            "section": sec,
            "ratio": round(ratio.value,3)
        }

    def GetSupportReactionsIfAvailable(self, support_node, load_case):

        # Only read reactions when the analysis results exist
        if not self.AreResultsAvailable():
            return None

        return self.GetSupportReactions(support_node, load_case)

    def GetMemberEndForcesGlobal(self, member_no, end_no, load_case):

        # Member end forces / moments in LOCAL axes
        fx, fy, fz, mx, my, mz = self.GetMemberEndForces(
            member_no,
            end_no,
            load_case
        )

        # Member local axis triad (direction cosines, beta applied)
        axes = self.geometry.GetBeamLocalAxisCosines(member_no)
        lx = axes["local_x"]
        ly = axes["local_y"]
        lz = axes["local_z"]

        # Rotate a local vector into global using the axis cosines
        def to_global(vx, vy, vz):
            gx = vx * lx[0] + vy * ly[0] + vz * lz[0]
            gy = vx * lx[1] + vy * ly[1] + vz * lz[1]
            gz = vx * lx[2] + vy * ly[2] + vz * lz[2]
            return gx, gy, gz

        Fx, Fy, Fz = to_global(fx, fy, fz)
        Mx, My, Mz = to_global(mx, my, mz)

        return tuple(round(v, 3) + 0.0 for v in (Fx, Fy, Fz, Mx, My, Mz))