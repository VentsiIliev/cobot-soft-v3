import time
from src.backend.GlueDispensingApplication import CompareContours
from src.backend.GlueDispensingApplication.utils.contours import close_contours_if_open
class WorkpieceMatcher:
    def __init__(self, application):
        self.application = application

    def perform_matching(self,debug=False):
        workpieces = self.application.get_workpieces()
        time.sleep(2)
        matches = self.__get_matches( workpieces, debug)
        return matches

    def __get_matches(self, workpieces, debug=False):
        newContours = self.application.visionService.contours
        if newContours is None:
            return False, "No contours found"
        closed_contours = close_contours_if_open(newContours)

        matches_data, noMatches, _ = CompareContours.findMatchingWorkpieces(workpieces, closed_contours)
        matches = matches_data["workpieces"]
        return matches
