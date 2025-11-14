import time
from backend.system.contour_matching import CompareContours
from backend.system.utils.contours import close_contours_if_open
class WorkpieceMatcher:
    def __init__(self):
        pass
    def perform_matching(self,workpieces,new_contours,debug=False):
        matches = self.__get_matches( workpieces, new_contours, debug)
        return matches

    def __get_matches(self, workpieces, new_contours, debug=False):
        if new_contours is None:
            return False, "No contours found"
        closed_contours = close_contours_if_open(new_contours)

        matches_data, noMatches, _ = CompareContours.findMatchingWorkpieces(workpieces, closed_contours)
        matches = matches_data["workpieces"]
        return matches

