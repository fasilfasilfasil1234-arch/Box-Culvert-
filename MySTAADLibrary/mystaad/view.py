class View:

    def __init__(self, staad):

        self.view = staad.View

        self.view._FlagAsMethod("CreateNewViewForSelections")

    def CreateNewViewForSelections(self):

        self.view.CreateNewViewForSelections()
