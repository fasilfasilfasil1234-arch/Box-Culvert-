class Analysis:

    def __init__(self, staad):

        self.staad = staad

        self.staad._FlagAsMethod("Analyze")

    def Analyze(self):

        self.staad.Analyze()
