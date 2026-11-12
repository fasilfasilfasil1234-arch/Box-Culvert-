import pythoncom
from win32com.client import VARIANT


class Support:

    def __init__(self, staad):

        self.support = staad.Support

        self.support._FlagAsMethod("CreateSupportPinned")
        self.support._FlagAsMethod("AssignSupportToNode")
        self.support._FlagAsMethod("GetSupportCount")
        self.support._FlagAsMethod("GetSupportNodes")

    def CreateSupportPinned(self):

        return self.support.CreateSupportPinned()

    def AssignSupportToNode(self, node_no, support):

        return self.support.AssignSupportToNode(node_no, support)

    def GetSupportCount(self):

        return int(self.support.GetSupportCount())

    def GetSupportNodes(self):

        count = self.GetSupportCount()

        if count == 0:
            return []

        nodes = VARIANT(
            pythoncom.VT_ARRAY | pythoncom.VT_BYREF | pythoncom.VT_I4,
            [0] * count
        )

        self.support.GetSupportNodes(nodes)

        return list(nodes.value)
