import win32com.client

from .result import Results
from .geometry import Geometry
from .load import Load
from .analysis import Analysis
from .support import Support
from .view import View


class OpenSTAAD:

    def __init__(self):

        self.staad = win32com.client.GetObject(
            None,
            "StaadPro.OpenSTAAD"
        )

        self.geometry = Geometry(self.staad)
        self.results = Results(self.staad, self.geometry)
        self.load = Load(self.staad)
        self.analysis = Analysis(self.staad)
        self.support = Support(self.staad)
        self.view = View(self.staad)

    def AssignPinnedSupportToSelectedNodes(self):

        # Get the currently selected nodes
        nodes = self.geometry.GetSelectedNodes()

        if not nodes:
            return {
                "assigned_nodes": [],
                "support_nodes": [],
                "message": "No nodes are currently selected."
            }

        # Create one pinned support definition
        pinned = self.support.CreateSupportPinned()

        # Assign it to every selected node
        for node_no in nodes:
            self.support.AssignSupportToNode(node_no, pinned)

        # Read back the full list of support nodes and open a new view
        support_nodes = self.support.GetSupportNodes()
        self.view.CreateNewViewForSelections()

        return {
            "assigned_nodes": list(nodes),
            "support_nodes": support_nodes
        }